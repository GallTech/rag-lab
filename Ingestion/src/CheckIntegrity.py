import boto3
import psycopg2
import os

# === Config ===
PG_HOST = "192.168.0.11"
PG_DB = "raglab"
PG_USER = "placeholder"
PG_PASSWORD = os.environ.get("PG_PASSWORD")

MINIO_URL = "http://192.168.0.17:9000"
MINIO_ACCESS = "admin"
MINIO_SECRET = "placeholder"
MINIO_BUCKET = "placeholder"

# === Connect to PostgreSQL ===
pg_conn = psycopg2.connect(
    host=PG_HOST,
    dbname=PG_DB,
    user=PG_USER,
    password=PG_PASSWORD
)
pg_cursor = pg_conn.cursor()
pg_cursor.execute("SELECT pdf_key FROM openalex_works WHERE pdf_key IS NOT NULL;")
pg_keys = set(row[0] for row in pg_cursor.fetchall())

# === Connect to MinIO ===
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_URL,
    aws_access_key_id=MINIO_ACCESS,
    aws_secret_access_key=MINIO_SECRET
)

# === Get all keys from MinIO ===
minio_keys = set()
paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=MINIO_BUCKET):
    for obj in page.get("Contents", []):
        minio_keys.add(obj["Key"])

# === Output comparison ===
all_keys = sorted(pg_keys | minio_keys)
print(f"{'MinIO':<10} | {'Postgres':<10} | Key")
print("-" * 40)

for key in all_keys:
    m = "✅" if key in minio_keys else "❌"
    p = "✅" if key in pg_keys else "❌"
    print(f"{m:<10} | {p:<10} | {key}")

pg_cursor.close()
pg_conn.close()
