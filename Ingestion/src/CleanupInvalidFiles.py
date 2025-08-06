import os
import boto3
import psycopg2

# === MinIO Config ===
MINIO_ENDPOINT = "http://192.168.0.17:9000"
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

# === Initialize MinIO client ===
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

# === Count PDFs in MinIO ===
def count_pdfs_in_minio():
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=MINIO_BUCKET)

    count = 0
    for page in page_iterator:
        count += page.get("KeyCount", 0)

    return count

# === Delete all PDFs from MinIO ===
def delete_all_pdfs_from_minio():
    deleted = 0
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=MINIO_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".pdf"):
                s3.delete_object(Bucket=MINIO_BUCKET, Key=key)
                deleted += 1
                print(f"🗑️ Deleted: {key}")

    print(f"\n✅ Total PDFs deleted from MinIO: {deleted}")

# === Count JSON entries in Postgres ===
def count_json_in_postgres():
    conn = psycopg2.connect(
        host=PG_HOST,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
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
        host=PG_HOST,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT work_id) FROM chunks;")
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

    try:
        postgres_count = count_json_in_postgres()
        print(f"🧠 JSON metadata in PostgreSQL: {postgres_count}")
    except Exception as e:
        print(f"❌ Error accessing PostgreSQL (metadata): {e}")

    try:
        chunked_count = count_unique_chunked_papers()
        print(f"📑 Distinct chunked papers: {chunked_count}")
    except Exception as e:
        print(f"❌ Error accessing PostgreSQL (chunks): {e}")

    confirm = input("\n⚠️  Do you want to DELETE ALL PDFs from MinIO? Type 'YES' to confirm: ")
    if confirm == "YES":
        delete_all_pdfs_from_minio()
    else:
        print("❌ PDF deletion cancelled.")