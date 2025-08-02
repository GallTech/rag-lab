import os
import json
import psycopg2
import boto3
from datetime import datetime

# === Config ===
PDF_DIR = os.path.expanduser("~/staging/pdfs")
META_DIR = os.path.expanduser("~/staging/metadata")
LOG_DIR = "/home/mike/rag-logs"
LOG_FILE = os.path.join(LOG_DIR, f"ingest_log_{datetime.now().isoformat()}.log")

MINIO_ENDPOINT = "192.168.0.17:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "adminsecret"
MINIO_BUCKET = "papers"

PG_HOST = "192.168.0.11"
PG_USER = "mike"
PG_DB = "raglab"
PG_PASSWORD = os.getenv("PG_PASSWORD")  # ✅ Use env variable
if not PG_PASSWORD:
    raise RuntimeError("❌ PG_PASSWORD environment variable not set.")

os.makedirs(LOG_DIR, exist_ok=True)

# === Connect to Postgres ===
pg_conn = psycopg2.connect(
    host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
)
pg_cur = pg_conn.cursor()
pg_cur.execute("SELECT id FROM openalex_works;")
existing_ids = set(row[0] for row in pg_cur.fetchall())

# === Connect to MinIO ===
s3 = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

# === Logger ===
def log(reason, file_id):
    with open(LOG_FILE, "a") as logf:
        logf.write(f"{file_id}: {reason}\n")

# === Check if file exists in MinIO ===
def file_exists_in_minio(key):
    try:
        s3.head_object(Bucket=MINIO_BUCKET, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False

# === Main Upload Loop ===
uploaded = 0
skipped = 0
for filename in os.listdir(PDF_DIR):
    if not filename.endswith(".pdf"):
        continue

    file_id = os.path.splitext(filename)[0]
    paper_id = f"https://openalex.org/{file_id}"
    pdf_path = os.path.join(PDF_DIR, filename)
    json_path = os.path.join(META_DIR, f"{file_id}.json")

    # --- Step 1: Require JSON ---
    if not os.path.isfile(json_path):
        log("missing_json", file_id)
        continue

    # --- Step 2: Check if already uploaded ---
    if paper_id in existing_ids:
        log("already_in_postgres", file_id)
        skipped += 1
        continue

    if file_exists_in_minio(filename):
        log("already_in_minio", file_id)
        skipped += 1
        continue

    # --- Step 3: Upload to MinIO ---
    try:
        s3.upload_file(pdf_path, MINIO_BUCKET, filename)
    except Exception as e:
        log(f"upload_failed: {e}", file_id)
        continue

    # --- Step 4: Insert to Postgres ---
    try:
        with open(json_path) as f:
            work = json.load(f)
        pg_cur.execute(
            "INSERT INTO openalex_works (id, title, full_raw, pdf_key) VALUES (%s, %s, %s, %s)",
            (work["id"], work.get("title", ""), json.dumps(work), filename),
        )
        pg_conn.commit()
        uploaded += 1
        print(f"✅ {file_id} → Postgres + MinIO")
    except Exception as e:
        log(f"postgres_insert_failed: {e}", file_id)
        pg_conn.rollback()

# === Final Report ===
print(f"\n✅ Done: {uploaded} uploaded, {skipped} skipped.")
print(f"📄 Log: {LOG_FILE}")

pg_cur.close()
pg_conn.close()