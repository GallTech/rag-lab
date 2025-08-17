#!/usr/bin/env python3
import os
import boto3
import psycopg2
import requests

# === CONFIG ===
PG_CONFIG = dict(
    host="192.168.0.11",
    dbname="raglab",
    user="mike",
    password=os.getenv("PG_PASSWORD"),
)
MINIO_ENDPOINT = "http://192.168.0.17:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "adminsecret"
MINIO_BUCKET = "papers"
QDRANT_URL = "http://192.168.0.11:6333"
QDRANT_COLLECTION = "openalex"

# === Helpers ===
def pg_conn():
    return psycopg2.connect(**PG_CONFIG)

def fetch_pg_works():
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM openalex_works;")
        return set(r[0] for r in cur.fetchall())

def fetch_pg_chunks():
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT DISTINCT work_id FROM chunks;")
        return set(r[0] for r in cur.fetchall())

def fetch_minio_ids():
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )
    paginator = s3.get_paginator("list_objects_v2")
    ids = set()
    for page in paginator.paginate(Bucket=MINIO_BUCKET):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".pdf"):
                base = os.path.splitext(os.path.basename(obj["Key"]))[0]
                ids.add(f"https://openalex.org/{base}")
    return ids

def fetch_qdrant_ids():
    ids = set()
    offset = None
    while True:
        payload = {
            "limit": 1000,
            "with_payload": True,
            "with_vector": False
        }
        if offset:
            payload["offset"] = offset
        r = requests.post(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/scroll", json=payload)
        r.raise_for_status()
        data = r.json().get("result", {})
        points = data.get("points", [])
        for p in points:
            wid = p.get("payload", {}).get("work_id")
            if wid:
                ids.add(wid)
        if not data.get("next_page_offset"):
            break
        offset = data["next_page_offset"]
    return ids

# === Main ===
def main():
    print("🔍 Auditing pipeline consistency...\n")

    works_pg = fetch_pg_works()
    chunks_pg = fetch_pg_chunks()
    pdfs_minio = fetch_minio_ids()
    embeds_qdrant = fetch_qdrant_ids()

    print(f"📄 Postgres works     : {len(works_pg)}")
    print(f"🧩 Postgres chunks    : {len(chunks_pg)} (distinct work_id)")
    print(f"📦 MinIO PDFs         : {len(pdfs_minio)}")
    print(f"🧠 Qdrant embeddings  : {len(embeds_qdrant)} (distinct work_id)\n")

    # Missing relationships
    missing_pdfs = works_pg - pdfs_minio
    missing_works = pdfs_minio - works_pg
    missing_chunks = works_pg - chunks_pg
    missing_embeds = works_pg - embeds_qdrant

    print("=== Gaps Detected ===")
    if missing_pdfs:
        print(f"❌ Works in PG missing PDFs: {len(missing_pdfs)}")
    if missing_works:
        print(f"❌ PDFs in MinIO not in PG works: {len(missing_works)}")
    if missing_chunks:
        print(f"❌ Works in PG missing chunks: {len(missing_chunks)}")
    if missing_embeds:
        print(f"❌ Works in PG missing embeddings: {len(missing_embeds)}")

    if not any([missing_pdfs, missing_works, missing_chunks, missing_embeds]):
        print("✅ All sets align perfectly (work_id matches across systems)")

if __name__ == "__main__":
    main()
