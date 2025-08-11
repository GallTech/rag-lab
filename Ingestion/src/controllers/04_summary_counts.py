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

# === Count JSON entries in Postgres ===
def count_json_in_postgres():
    conn = psycopg2.connect(
        host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM openalex_works;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

# === Count distinct chunked work_ids in Postgres ===
def count_unique_chunked_papers():
    conn = psycopg2.connect(
        host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT work_id) FROM chunks;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

# === Count distinct embedded work_ids in Postgres ===
def count_unique_embedded_papers():
    conn = psycopg2.connect(
        host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(DISTINCT work_id) FROM chunks WHERE embedded = TRUE;"
    )
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

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
        embedded_count = count_unique_embedded_papers()
        print(f"🔗 Distinct embedded papers: {embedded_count}")
        if chunked_count is not None:
            remaining = chunked_count - embedded_count
            pct = (embedded_count / chunked_count * 100) if chunked_count > 0 else 0
            print(f"📊 Embedding progress: {embedded_count}/{chunked_count} "
                  f"({pct:.2f}%) — Remaining: {remaining}")
    except Exception as e:
        print(f"❌ Error accessing PostgreSQL (embedded): {e}")