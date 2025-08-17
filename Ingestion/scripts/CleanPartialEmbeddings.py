#!/usr/bin/env python3
import os
import sys
import argparse
import psycopg2
from psycopg2.extras import execute_values

# pip install qdrant-client
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

# ---------- CLI ----------
parser = argparse.ArgumentParser(description="Delete partial embeddings from Qdrant and reset flags in Postgres.")
parser.add_argument("--collection", required=True, help="Qdrant collection name (e.g., papers_chunks_v1_2048c_512o)")
parser.add_argument("--qdrant-host", default=os.getenv("QDRANT_HOST", "localhost"))
parser.add_argument("--qdrant-port", type=int, default=int(os.getenv("QDRANT_PORT", "6333")))
parser.add_argument("--qdrant-api-key", default=os.getenv("QDRANT_API_KEY"))
parser.add_argument("--batch-size", type=int, default=200, help="How many work_ids to delete per DB/UI batch (Qdrant deletes are per-id in this script).")
parser.add_argument("--dry-run", action="store_true", help="List what would be deleted/updated without doing it.")
args = parser.parse_args()

# ---------- Postgres config ----------
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "192.168.0.11"),
    "dbname": os.getenv("PG_DB", "raglab"),
    "user": os.getenv("PG_USER", "mike"),
    "password": os.getenv("PG_PASSWORD"),
}
if not PG_CONFIG["password"]:
    print("❌ PG_PASSWORD not set.", file=sys.stderr)
    sys.exit(1)

# ---------- Helpers ----------
def pg_connect():
    return psycopg2.connect(**PG_CONFIG)

def fetch_partial_work_ids():
    """
    Partials = work_ids with at least one embedded chunk and not all embedded.
    """
    sql = """
        SELECT work_id
        FROM chunks
        GROUP BY work_id
        HAVING SUM(CASE WHEN embedded THEN 1 ELSE 0 END) > 0
           AND   SUM(CASE WHEN embedded THEN 1 ELSE 0 END) < COUNT(*);
    """
    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [r[0] for r in rows]

def reset_embedded_flags(partial_ids):
    """
    Set embedded = FALSE for all chunks of those work_ids.
    """
    if not partial_ids:
        return 0
    sql = "UPDATE chunks SET embedded = FALSE WHERE work_id = ANY(%s);"
    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (partial_ids,))
        conn.commit()
    return len(partial_ids)

def delete_from_qdrant(client: QdrantClient, collection: str, work_id: str):
    """
    Delete all points whose payload has work_id == given id.
    Uses a payload filter (must match field 'work_id' exactly).
    """
    filt = qm.Filter(
        must=[
            qm.FieldCondition(
                key="work_id",
                match=qm.MatchValue(value=work_id)
            )
        ]
    )
    # wait=True blocks until applied
    return client.delete(collection_name=collection, points_selector=filt, wait=True)

# ---------- Main ----------
def main():
    print(f"🔎 Scanning Postgres for partially embedded papers ...")
    partial_ids = fetch_partial_work_ids()
    total_partials = len(partial_ids)
    print(f"Found {total_partials} partial work_ids.")

    if total_partials == 0:
        print("🎉 Nothing to clean. All chunked papers are fully embedded.")
        return

    if args.dry_run:
        show = min(10, total_partials)
        print(f"🚧 DRY RUN: would delete vectors in Qdrant and reset embedded flags for {total_partials} work_ids.")
        print("Examples:", *partial_ids[:show], sep="\n  - ")
        return

    # Connect to Qdrant
    client = QdrantClient(
        host=args.qdrant_host,
        port=args.qdrant_port,
        api_key=args.qdrant_api_key
    )

    # Delete vectors per work_id (simple & reliable; can be parallelized later if needed)
    print(f"🧹 Deleting vectors from Qdrant collection '{args.collection}' ...")
    done = 0
    for wid in partial_ids:
        try:
            _res = delete_from_qdrant(client, args.collection, wid)
        except Exception as e:
            print(f"⚠️  Qdrant delete failed for {wid}: {e}", file=sys.stderr)
            # Continue; we still reset flags so they get re-embedded cleanly later
        done += 1
        if done % 200 == 0 or done == total_partials:
            print(f"   ... {done}/{total_partials} deleted")

    # Reset embedded flags in Postgres
    print("🗂  Resetting embedded flags in Postgres ...")
    updated = reset_embedded_flags(partial_ids)
    print(f"✅ Done. Reset embedded flags for {updated} work_ids.")

    print("\nSummary:")
    print(f"  • Qdrant collection: {args.collection}")
    print(f"  • Partials processed: {total_partials}")
    print("  • Next: re-embed these papers (or leave them for the clean v2 run).")

if __name__ == "__main__":
    main()
