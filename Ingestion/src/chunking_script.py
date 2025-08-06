import os
import fitz  # PyMuPDF
import psycopg2
import boto3
from langchain.text_splitter import RecursiveCharacterTextSplitter
from uuid import uuid4
from datetime import datetime
from io import BytesIO

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

CHUNK_SIZE = 2048
CHUNK_OVERLAP = 512

if not PG_CONFIG["password"]:
    raise RuntimeError("❌ PG_PASSWORD not set.")

# === Text Splitter ===
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " "]
)

# === MinIO Client ===
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

# === PDF Text Extractor ===
def extract_text_from_pdf_bytes(pdf_bytes):
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        text = "\n".join(page.get_text() for page in doc)
    return text.replace('\x00', '')  # 🔧 Remove NUL bytes

# === Check if work_id already chunked ===
def is_already_chunked(work_id):
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM chunks WHERE work_id = %s LIMIT 1;", (work_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

# === Check if work_id exists in openalex_works ===
def work_id_exists(work_id):
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM openalex_works WHERE id = %s LIMIT 1;", (work_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

# === DB Insertion ===
def insert_chunks(work_id, chunks):
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    for idx, chunk in enumerate(chunks):
        clean_text = chunk['text'].replace('\x00', '')  # 🔧 Remove NUL bytes
        chunk_id = str(uuid4())
        cur.execute("""
            INSERT INTO chunks (id, work_id, chunk_index, text, char_start, char_end, token_count, embedded, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE, %s);
        """, (
            chunk_id,
            work_id,
            idx,
            clean_text,
            chunk['start'],
            chunk['end'],
            chunk['tokens'],
            datetime.utcnow()
        ))
    conn.commit()
    cur.close()
    conn.close()

# === Process a single PDF from MinIO ===
def process_pdf_from_minio(work_id, key):
    response = s3.get_object(Bucket=MINIO_BUCKET, Key=key)
    pdf_bytes = response['Body'].read()
    raw_text = extract_text_from_pdf_bytes(pdf_bytes)
    splits = splitter.create_documents([raw_text])
    chunks = []
    char_pos = 0
    for doc in splits:
        text = doc.page_content.replace('\x00', '')  # 🔧 Redundant safeguard
        length = len(text)
        chunks.append({
            "text": text,
            "start": char_pos,
            "end": char_pos + length,
            "tokens": length // 4  # rough estimate
        })
        char_pos += length - CHUNK_OVERLAP
    insert_chunks(work_id, chunks)

# === Iterate through all PDFs in MinIO ===
def process_all_pdfs():
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=MINIO_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".pdf"):
                continue

            short_id = os.path.splitext(os.path.basename(key))[0]
            work_id = f"https://openalex.org/{short_id}"

            if is_already_chunked(work_id):
                print(f"⏭️  Already chunked: {short_id}")
                continue

            if not work_id_exists(work_id):
                print(f"⚠️  Skipping (missing in Postgres): {short_id}")
                continue

            print(f"🔍 Processing: {short_id} ...")
            try:
                process_pdf_from_minio(work_id, key)
                print(f"✅ Done: {short_id}")
            except Exception as e:
                print(f"❌ Error processing {short_id}: {e}")

# === Run ===
if __name__ == "__main__":
    process_all_pdfs()