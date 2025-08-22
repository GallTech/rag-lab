import os
import boto3
import psycopg2

# === Config ===
MINIO_ENDPOINT = "http://192.168.0.17:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "adminsecret"
MINIO_BUCKET = "papers"

PG_CONFIG = {
    "host": "192.168.0.11",
    "dbname": "raglab",
    "user": "mike",
    "password": os.getenv("PG_PASSWORD")
}

def connect_pg():
    return psycopg2.connect(**PG_CONFIG)

def main():
    print("🔍 Diagnosing chunking mismatches and cleaning up bad items...\n")

    # Connect to Postgres
    conn = connect_pg()
    cur = conn.cursor()

    # === Get all work_ids in chunks table ===
    cur.execute("SELECT DISTINCT work_id FROM chunks;")
    chunked_ids = set(row[0] for row in cur.fetchall())

    # === Get all ids from openalex_works ===
    cur.execute("SELECT id FROM openalex_works;")
    all_ids = set(row[0] for row in cur.fetchall())

    # === Get all keys from MinIO ===
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )
    paginator = s3.get_paginator("list_objects_v2")
    minio_ids = set()
    minio_keys = {}
    for page in paginator.paginate(Bucket=MINIO_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".pdf"):
                base = os.path.splitext(os.path.basename(key))[0]
                work_id = f"https://openalex.org/{base}"
                minio_ids.add(work_id)
                minio_keys[work_id] = key

    cur.close()

    # === Analysis ===
    never_chunked = (all_ids & minio_ids) - chunked_ids

    print(f"🧠 Metadata entries        : {len(all_ids)}")
    print(f"📦 PDFs in MinIO           : {len(minio_ids)}")
    print(f"🧩 Already chunked works   : {len(chunked_ids)}")
    print(f"🕳️  PDFs + metadata but not chunked: {len(never_chunked)}")

    if never_chunked:
        conn = connect_pg()
        cur = conn.cursor()
        for wid in sorted(never_chunked):
            pdf_key = minio_keys.get(wid)
            if pdf_key:
                try:
                    s3.delete_object(Bucket=MINIO_BUCKET, Key=pdf_key)
                    print(f"🗑️  Deleted PDF from MinIO: {pdf_key}")
                except Exception as e:
                    print(f"❌ Failed to delete {pdf_key} from MinIO: {e}")
            try:
                cur.execute("DELETE FROM openalex_works WHERE id = %s;", (wid,))
                print(f"🧹 Deleted metadata for: {wid}")
            except Exception as e:
                print(f"❌ Failed to delete metadata for {wid}: {e}")
        conn.commit()
        cur.close()
        conn.close()

    print("\n✅ Cleanup complete.")

if __name__ == "__main__":
    main()
