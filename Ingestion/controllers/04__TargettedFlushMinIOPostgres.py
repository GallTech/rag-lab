#!/usr/bin/env python3

"""
Purge low-relevance OpenAlex works from PostgreSQL and MinIO.

This script calculates each works AI concept score (from the 'concepts'
field in full_raw JSON), compares against a threshold (default 0.4), and
deletes those below it.

Supports dry-run (--whatif) and execution (--execute).
Deletion order: MinIO PDFs first, then Postgres rows.
Qdrant is not touched.
python3 purge_ai_low.py --threshold 0.35

"""

import os
import sys
import argparse
from typing import List, Tuple, Dict

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

# OpenAlex AI concept IDs sometimes appear with/without the full URI
AI_IDS = ('https://openalex.org/C154945302', 'C154945302')

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

# ---------- SQL ----------
# We compute AI score from full_raw::jsonb->'concepts'
AI_SCORE_CTE = """
WITH scores AS (
  SELECT
    w.id,
    w.pdf_key,
    COALESCE((
      SELECT MAX( (c->>'score')::numeric )
      FROM jsonb_array_elements( (w.full_raw)::jsonb->'concepts') AS c
      WHERE c->>'id' = ANY(%s)
    ), 0)::numeric AS ai_score
  FROM openalex_works w
)
"""

def fetch_counts(threshold: float) -> Dict[str, int]:
    sql = AI_SCORE_CTE + """
    SELECT
      COUNT(*) FILTER (WHERE ai_score < %s) AS to_delete,
      COUNT(*) FILTER (WHERE ai_score >= %s) AS to_keep,
      COUNT(*) AS total
    FROM scores;
    """
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (list(AI_IDS), threshold, threshold))
        row = cur.fetchone()
        return {"to_delete": row[0], "to_keep": row[1], "total": row[2]}

def fetch_candidates(threshold: float) -> List[Tuple[str, str]]:
    sql = AI_SCORE_CTE + """
    SELECT id, pdf_key
    FROM scores
    WHERE ai_score < %s;
    """
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (list(AI_IDS), threshold))
        return cur.fetchall()  # [(id, pdf_key), ...]

# ---------- MinIO ----------
def delete_minio_objects(keys: List[str]) -> Tuple[int, List[str]]:
    """Delete objects in batches of 1000. Return (deleted_count, failed_keys)."""
    if not keys:
        return 0, []

    s3 = s3_client()
    deleted_total = 0
    failed: List[str] = []

    chunk_size = 1000
    for i in range(0, len(keys), chunk_size):
        chunk = keys[i:i+chunk_size]
        resp = s3.delete_objects(
            Bucket=MINIO_BUCKET,
            Delete={"Objects": [{"Key": k} for k in chunk], "Quiet": True},
        )
        deleted_total += len(resp.get("Deleted", []))
        errs = resp.get("Errors", [])
        if errs:
            failed.extend([e.get("Key") for e in errs if e.get("Key")])

    return deleted_total, failed

# ---------- Postgres ----------
def delete_postgres_rows(ids: List[str]) -> int:
    if not ids:
        return 0
    sql = "DELETE FROM openalex_works WHERE id = ANY(%s);"
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (ids,))
        return cur.rowcount

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(
        description="Purge works with AI concept score below threshold from Postgres + MinIO (no Qdrant)."
    )
    ap.add_argument("--threshold", type=float, default=0.4, help="AI score cutoff (default: 0.4)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--whatif", action="store_true", help="Dry run (default if --execute not given).")
    g.add_argument("--execute", action="store_true", help="Actually delete from MinIO then Postgres.")
    args = ap.parse_args()

    threshold = args.threshold

    # Always show counts first
    counts = fetch_counts(threshold)
    to_del, to_keep, total = counts["to_delete"], counts["to_keep"], counts["total"]

    print(f"🧮 Threshold: AI score < {threshold}")
    print(f"📚 Total works in Postgres: {total}")
    print(f"🗑️  Would delete (<{threshold}): {to_del}")
    print(f"✅ Would keep (≥{threshold}): {to_keep}")

    if not args.execute:
        print("\n[WHATIF] No changes made. Use --execute to perform deletion.")
        return

    # Execute path
    print("\n⚠️ EXECUTION MODE: deleting from MinIO, then Postgres…")
    candidates = fetch_candidates(threshold)
    if not candidates:
        print("Nothing to delete. Exiting.")
        return

    ids_all = [w_id for (w_id, _) in candidates]
    keys_all = [k for (_, k) in candidates if k]  # skip NULL/empty keys

    # 1) Delete from MinIO
    deleted_count, failed_keys = delete_minio_objects(keys_all)
    print(f"🗂️ MinIO objects requested: {len(keys_all)}")
    print(f"🧽 MinIO objects deleted:  {deleted_count}")
    if failed_keys:
        print(f"⚠️ MinIO failed deletions: {len(failed_keys)}")

    # Only delete Postgres rows whose PDF we successfully removed (or had no pdf_key)
    ok_keys = set(keys_all) - set(failed_keys)
    ids_ok = [w_id for (w_id, k) in candidates if (not k) or (k in ok_keys)]

    rows_deleted = delete_postgres_rows(ids_ok)
    print(f"🧮 Postgres rows deleted: {rows_deleted}")

    # Final summary
    est_remaining = total - rows_deleted
    print("\n✅ Done.")
    print(f"📊 Summary: started {total} — deleted {rows_deleted} — remaining (est.) {est_remaining}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
