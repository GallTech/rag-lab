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

if not PG_CONFIG["password"]:
    raise RuntimeError("❌ PG_PASSWORD not set.")

# === Connect Clients ===
def connect_minio():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )

def connect_pg():
    return psycopg2.connect(**PG_CONFIG)

# === Check PostgreSQL structure ===
def check_postgres_schema():
    conn = connect_pg()
    cur = conn.cursor()

    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'openalex_works';")
    columns = {row[0] for row in cur.fetchall()}
    if "chunking_status" not in columns:
        print("❌ Missing column: chunking_status in openalex_works")
    else:
        print("✅ Found column: chunking_status")

    cur.execute("SELECT to_regclass('public.chunks');")
    if cur.fetchone()[0] is None:
        print("❌ Missing table: chunks")
    else:
        print("✅ Found table: chunks")

    cur.close()
    conn.close()

# === Check file + record matches ===
def verify_sync_between_minio_and_postgres():
    s3 = connect_minio()
    conn = connect_pg()
    cur = conn.cursor()

    # Get all PDFs in MinIO
    pdf_keys = set()
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=MINIO_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".pdf"):
                pdf_keys.add(key)

    # Get all openalex IDs from DB
    cur.execute("SELECT id, pdf_key, chunking_status FROM openalex_works;")
    db_rows = cur.fetchall()
    db_ids = {row[0].split('/')[-1] for row in db_rows}
    db_pdf_keys = {row[1] for row in db_rows if row[1]}

    # Check for mismatches
    minio_pdf_ids = {key.replace(".pdf", "") for key in pdf_keys}

    missing_in_db = sorted(minio_pdf_ids - db_ids)
    missing_in_minio = sorted(db_ids - minio_pdf_ids)

    print(f"\n🔍 PDFs in MinIO: {len(minio_pdf_ids)}")
    print(f"🧠 Metadata in Postgres: {len(db_ids)}")

    if missing_in_db:
        print(f"❌ PDFs with no DB entry: {len(missing_in_db)}")
        for wid in missing_in_db[:5]:
            print(f"   - {wid}.pdf")
    else:
        print("✅ All PDFs matched in DB.")

    if missing_in_minio:
        print(f"❌ DB entries with no PDF in MinIO: {len(missing_in_minio)}")
        for wid in missing_in_minio[:5]:
            print(f"   - {wid}.pdf")
    else:
        print("✅ All DB entries have PDFs in MinIO.")

    # Count chunking status
    status_counts = {"success": 0, "failed": 0, "pending": 0, "none": 0}
    for row in db_rows:
        status = row[2] or "none"
        status_counts[status] = status_counts.get(status, 0) + 1

    print("\n📊 Chunking status breakdown:")
    for status, count in status_counts.items():
        print(f"   {status}: {count}")

    cur.close()
    conn.close()

# === Main ===
if __name__ == "__main__":
    print("🔧 Checking PostgreSQL schema...")
    check_postgres_schema()
    print("\n🔍 Verifying PDF ↔ Metadata sync...")
    verify_sync_between_minio_and_postgres()