#!/usr/bin/env python3
import os
import boto3
import psycopg2

# === MinIO Config ===
MINIO_ENDPOINT = "192.168.0.17:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "adminsecret"
MINIO_BUCKET = "papers"

# === Postgres Config ===
PG_HOST = "192.168.0.11"
PG_DB = "raglab"
PG_USER = "mike"
PG_PASSWORD = os.getenv("PG_PASSWORD")

if not PG_PASSWORD:
    raise RuntimeError("❌ PG_PASSWORD environment variable not set.")

# === Count PDFs in MinIO ===
def count_pdfs_in_minio():
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )
    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=MINIO_BUCKET)

    count = 0
    for page in page_iterator:
        count += page.get("KeyCount", 0)
    return count

# === Postgres helpers ===
def _pg_conn():
    return psycopg2.connect(
        host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )

# === Count JSON entries in Postgres ===
def count_json_in_postgres():
    with _pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM openalex_works;")
        return cur.fetchone()[0]

# === Count distinct chunked work_ids in Postgres ===
def count_unique_chunked_papers():
    with _pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(DISTINCT work_id) FROM chunks;")
        return cur.fetchone()[0]

# === Count distinct embedded work_ids (ANY chunk embedded) ===
def count_any_embedded_papers():
    with _pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(DISTINCT work_id) FROM chunks WHERE embedded = TRUE;")
        return cur.fetchone()[0]

# === Count fully embedded papers (ALL chunks embedded) ===
def count_fully_embedded_papers():
    with _pg_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT work_id
                FROM chunks
                GROUP BY work_id
                HAVING BOOL_AND(embedded)  -- all chunks for this work_id are TRUE
            ) s;
            """
        )
        return cur.fetchone()[0]

# If BOOL_AND isn't available on your Postgres, replace the HAVING line with:
# HAVING COUNT(*) = COUNT(*) FILTER (WHERE embedded)

# === Main ===
if __name__ == "__main__":
    print("🔍 Checking system status...\n")

    try:
        minio_count = count_pdfs_in_minio()
        print(f"📦 PDFs in MinIO: {minio_count}")
    except Exception as e:
        print(f"❌ Error accessing MinIO: {e}")
        minio_count = None

    try:
        postgres_count = count_json_in_postgres()
        print(f"🧠 JSON metadata in PostgreSQL: {postgres_count}")
    except Exception as e:
        print(f"❌ Error accessing PostgreSQL (metadata): {e}")
        postgres_count = None

    try:
        chunked_count = count_unique_chunked_papers()
        print(f"📑 Distinct chunked papers: {chunked_count}")
    except Exception as e:
        print(f"❌ Error accessing PostgreSQL (chunks): {e}")
        chunked_count = None

    try:
        any_embedded = count_any_embedded_papers()
        print(f"🔗 Papers with ANY chunk embedded: {any_embedded}")
    except Exception as e:
        print(f"❌ Error accessing PostgreSQL (any embedded): {e}")
        any_embedded = None

    try:
        fully_embedded = count_fully_embedded_papers()
        print(f"🧩 Fully embedded papers (ALL chunks): {fully_embedded}")
    except Exception as e:
        print(f"❌ Error accessing PostgreSQL (fully embedded): {e}")
        fully_embedded = None

    # Progress summaries (if we have chunked_count)
    if chunked_count and chunked_count > 0:
        if any_embedded is not None:
            pct_any = any_embedded / chunked_count * 100
            remaining_any = max(chunked_count - any_embedded, 0)
            print(
                f"📊 Any-embed progress: {any_embedded}/{chunked_count} "
                f"({pct_any:.2f}%) — Remaining (any): {remaining_any}"
            )

        if fully_embedded is not None:
            pct_full = fully_embedded / chunked_count * 100
            remaining_full = max(chunked_count - fully_embedded, 0)
            print(
                f"📈 Full-embed progress: {fully_embedded}/{chunked_count} "
                f"({pct_full:.2f}%) — Remaining (full): {remaining_full}"
            )