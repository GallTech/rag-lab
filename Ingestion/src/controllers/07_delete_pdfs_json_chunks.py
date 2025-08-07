# ResetPipeline.py
import boto3
import psycopg2
import os
import argparse

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

def reset(confirm=False):
    if not confirm:
        print("⚠️  Add --confirm to actually run the reset.")
        return

    print("🧨 Resetting pipeline...")

    # MinIO: delete all PDFs
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )
    response = s3.list_objects_v2(Bucket=MINIO_BUCKET)
    if "Contents" in response:
        for obj in response["Contents"]:
            key = obj["Key"]
            s3.delete_object(Bucket=MINIO_BUCKET, Key=key)
            print(f"🗑️  Deleted from MinIO: {key}")

    # PostgreSQL: delete all metadata + chunks
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    cur.execute("DELETE FROM chunks;")
    cur.execute("DELETE FROM openalex_works;")
    conn.commit()
    cur.close()
    conn.close()
    print("✅ All database entries wiped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="Actually perform the reset")
    args = parser.parse_args()
    reset(confirm=args.confirm)