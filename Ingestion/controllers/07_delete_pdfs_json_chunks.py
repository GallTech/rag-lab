# ResetPipeline.py
import boto3
import psycopg2
import os
import argparse
import requests

# MinIO config
MINIO_ENDPOINT = "http://192.168.0.17:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "adminsecret"
MINIO_BUCKET = "papers"

# PostgreSQL config
PG_CONFIG = {
    "host": "192.168.0.11",
    "dbname": "raglab",
    "user": "mike",
    "password": os.getenv("PG_PASSWORD")
}

# Qdrant config
QDRANT_URL = "http://192.168.0.11:6333"
QDRANT_COLLECTION = "openalex"

def empty_minio_bucket():
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )
    paginator = s3.get_paginator("list_objects_v2")
    total_deleted = 0
    for page in paginator.paginate(Bucket=MINIO_BUCKET):
        contents = page.get("Contents", [])
        if not contents:
            continue
        # Batch delete up to 1000 keys per request
        for i in range(0, len(contents), 1000):
            batch = [{"Key": obj["Key"]} for obj in contents[i:i+1000]]
            s3.delete_objects(Bucket=MINIO_BUCKET, Delete={"Objects": batch})
            total_deleted += len(batch)
            print(f"🗑️  Deleted {total_deleted} objects from MinIO so far...")
    if total_deleted == 0:
        print("ℹ️  MinIO bucket already empty.")

def reset(confirm=False):
    if not confirm:
        print("⚠️  Add --confirm to actually run the reset.")
        return

    print("🧨 Resetting pipeline...")

    # Qdrant: delete embeddings collection
    try:
        resp = requests.delete(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}", timeout=30)
        if resp.status_code in (200, 202):
            print(f"🗑️  Qdrant: collection '{QDRANT_COLLECTION}' deleted.")
        elif resp.status_code == 404:
            print(f"ℹ️  Qdrant: collection '{QDRANT_COLLECTION}' not found (already gone).")
        else:
            print(f"❌ Qdrant delete returned {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"❌ Qdrant delete error: {e}")

    # MinIO: delete ALL PDFs (paginated)
    try:
        empty_minio_bucket()
    except Exception as e:
        print(f"❌ MinIO delete error: {e}")

    # PostgreSQL: delete all metadata + chunks
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        cur.execute("DELETE FROM chunks;")
        cur.execute("DELETE FROM openalex_works;")
        conn.commit()
        cur.close()
        conn.close()
        print("✅ All database entries wiped.")
    except Exception as e:
        print(f"❌ Postgres delete error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="Actually perform the reset")
    args = parser.parse_args()
    reset(confirm=args.confirm)