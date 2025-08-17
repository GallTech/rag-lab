#!/usr/bin/env python3
import os
import sys
import csv
import argparse
from typing import Dict, Set, Tuple, List

import boto3
import psycopg2

# === Config (env overrides allowed) ===
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://192.168.0.17:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "adminsecret")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "papers")

PG_HOST = os.getenv("PG_HOST", "192.168.0.11")
PG_DB = os.getenv("PG_DB", "raglab")
PG_USER = os.getenv("PG_USER", "mike")
PG_PASSWORD = os.getenv("PG_PASSWORD")

if not PG_PASSWORD:
    raise RuntimeError("❌ PG_PASSWORD environment variable not set.")

# ---------- Clients ----------
def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )

def pg_conn():
    return psycopg2.connect(host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD)

# ---------- MinIO listing ----------
def list_minio_objects(bucket: str) -> Tuple[Dict[str, int], int, int]:
    """
    Return (sizes_by_key, total_objects, total_bytes)
    sizes_by_key: {key: size_in_bytes}
    """
    s3 = s3_client()
    paginator = s3.get_paginator("list_objects_v2")
    sizes: Dict[str, int] = {}
    total = 0
    total_bytes = 0
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []) or []:
            key = obj["Key"]
            size = obj.get("Size", 0)
            sizes[key] = size
            total += 1
            total_bytes += size
    return sizes, total, total_bytes

# ---------- Postgres ----------
def fetch_db_pdf_keys() -> Tuple[Set[str], Dict[str, str]]:
    """
    Returns:
      keys_in_db: set of pdf_key strings
      id_by_key: map pdf_key -> id (for convenience/backrefs)
    """
    sql = "SELECT id, pdf_key FROM openalex_works WHERE pdf_key IS NOT NULL;"
    keys: Set[str] = set()
    id_by_key: Dict[str, str] = {}
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        for _id, pdf_key in cur.fetchall():
            if pdf_key:
                keys.add(pdf_key)
                # If duplicates exist, last one wins; fine for reporting
                id_by_key[pdf_key] = _id
    return keys, id_by_key

# ---------- CSV helpers ----------
def export_list(path: str, rows: List[List]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# ---------- Delete MinIO keys ----------
def delete_minio_keys(keys: List[str]) -> Tuple[int, List[str]]:
    s3 = s3_client()
    deleted = 0
    failed: List[str] = []
    CHUNK = 1000
    for i in range(0, len(keys), CHUNK):
        chunk = keys[i:i+CHUNK]
        resp = s3.delete_objects(
            Bucket=MINIO_BUCKET,
            Delete={"Objects": [{"Key": k} for k in chunk], "Quiet": False},  # show Deleted / Errors
        )
        deleted += len(resp.get("Deleted", []))
        for e in resp.get("Errors", []) or []:
            if e.get("Key"):
                failed.append(e["Key"])
    return deleted, failed

def human_bytes(n: int) -> str:
    # simple IEC units
    for unit in ["B","KiB","MiB","GiB","TiB"]:
        if n < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024

def main():
    ap = argparse.ArgumentParser(description="Reconcile MinIO objects with Postgres pdf_key references.")
    ap.add_argument("--export-prefix", type=str, default=None,
                    help="If set, export CSVs: <prefix>_minio_orphans.csv and <prefix>_db_missing.csv")
    ap.add_argument("--delete-minio-orphans", action="store_true",
                    help="Delete MinIO objects that are not referenced in Postgres.")
    args = ap.parse_args()

    print("🔎 Reconciling MinIO vs Postgres…\n")

    # List MinIO
    sizes_by_key, minio_count, minio_bytes = list_minio_objects(MINIO_BUCKET)
    print(f"🗂️  MinIO objects in '{MINIO_BUCKET}': {minio_count} ({human_bytes(minio_bytes)})")

    # Load DB keys
    db_keys, id_by_key = fetch_db_pdf_keys()
    print(f"🧠 Postgres rows with pdf_key: {len(db_keys)}")

    # Diff
    minio_keys: Set[str] = set(sizes_by_key.keys())
    minio_only = sorted(list(minio_keys - db_keys))      # orphans in MinIO
    db_only    = sorted(list(db_keys - minio_keys))      # DB rows whose file missing in MinIO

    minio_only_bytes = sum(sizes_by_key[k] for k in minio_only)
    print(f"\n❗ MinIO orphans (in MinIO, not in DB): {len(minio_only)} "
          f"({human_bytes(minio_only_bytes)})")
    print(f"❗ DB-only (in DB, missing in MinIO): {len(db_only)}")

    # Optional export
    if args.export_prefix:
        mo_path = f"{args.export_prefix}_minio_orphans.csv"
        dbm_path = f"{args.export_prefix}_db_missing.csv"

        export_list(mo_path, [["key","size_bytes","size_human"]] +
                    [[k, sizes_by_key[k], human_bytes(sizes_by_key[k])] for k in minio_only])
        export_list(dbm_path, [["pdf_key","id"]] +
                    [[k, id_by_key.get(k, "")] for k in db_only])

        print(f"\n💾 Exported:")
        print(f"   - MinIO orphans → {mo_path}")
        print(f"   - DB-missing    → {dbm_path}")

    # Optional delete MinIO orphans
    if args.delete_minio_orphans and minio_only:
        print("\n⚠️ Deleting MinIO orphans (unreferenced objects)…")
        deleted, failed = delete_minio_keys(minio_only)
        print(f"🧽 Deleted from MinIO: {deleted}")
        if failed:
            print(f"⚠️ Failed deletions: {len(failed)}")
            # Optional: export failures
            if args.export_prefix:
                failed_path = f"{args.export_prefix}_minio_delete_failed.csv"
                export_list(failed_path, [["key"]] + [[k] for k in failed])
                print(f"   • Failed list saved to {failed_path}")

    print("\n✅ Reconcile complete.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
