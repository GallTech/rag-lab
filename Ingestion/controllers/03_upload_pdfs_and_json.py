import os
import json
import boto3
import psycopg2
import logging

# === Config ===
MINIO_ENDPOINT = "http://192.168.0.17:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "adminsecret"
MINIO_BUCKET = "papers"

PG_HOST = "192.168.0.11"
PG_DB = "raglab"
PG_USER = "mike"
PG_PASSWORD = os.getenv("PG_PASSWORD")

PDF_DIR = os.path.expanduser("~/staging/pdfs")
META_DIR = os.path.expanduser("~/staging/metadata")

# === Check env ===
if not PG_PASSWORD:
    raise RuntimeError("❌ PG_PASSWORD environment variable not set.")

# === Setup Logging (stdout only) ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]  # only stdout
)

# === Clients ===
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

pg_conn = psycopg2.connect(
    host=PG_HOST,
    dbname=PG_DB,
    user=PG_USER,
    password=PG_PASSWORD
)
pg_cur = pg_conn.cursor()

# === Load existing IDs from DB ===
def get_existing_ids():
    pg_cur.execute("SELECT id FROM openalex_works;")
    return set(r[0] for r in pg_cur.fetchall())

# === Upload matching pairs ===
def upload_all():
    existing_ids = get_existing_ids()
    uploaded = 0
    skipped = 0
    failed = 0

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    for pdf_file in pdf_files:
        base_id = pdf_file.replace(".pdf", "")
        json_path = os.path.join(META_DIR, f"{base_id}.json")
        pdf_path = os.path.join(PDF_DIR, pdf_file)

        if not os.path.exists(json_path):
            logging.warning(f"⚠️ JSON not found for {base_id}, skipping.")
            skipped += 1
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            work_id = data["id"]
            if work_id in existing_ids:
                logging.info(f"⏩ Skipping {work_id}, already in database.")
                skipped += 1
                continue

            title = data.get("title", None)
            full_raw = json.dumps(data)
            pdf_key = f"{base_id}.pdf"

            # Upload PDF to MinIO
            s3.upload_file(pdf_path, MINIO_BUCKET, pdf_key)

            # Insert metadata into Postgres
            pg_cur.execute("""
                INSERT INTO openalex_works (id, title, full_raw, pdf_key)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """, (work_id, title, full_raw, pdf_key))

            pg_conn.commit()
            uploaded += 1
            logging.info(f"✅ Uploaded: {pdf_file} + {base_id}.json")

        except Exception as e:
            failed += 1
            logging.error(f"❌ Failed for {base_id}: {e}")

    logging.info(f"\n📦 PDFs uploaded: {uploaded}")
    logging.info(f"⏩ Skipped: {skipped}")
    logging.info(f"❌ Failed: {failed}")

# === Run ===
if __name__ == "__main__":
    logging.info("🚀 Starting upload process...\n")
    upload_all()
    pg_cur.close()
    pg_conn.close()
    logging.info("✅ Upload complete.")
