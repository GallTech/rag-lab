#!/usr/bin/env python3
import psycopg2
import os
import sys

PG_CONFIG = dict(
    host="192.168.0.11",
    dbname="raglab",
    user="mike",
    password=os.getenv("PG_PASSWORD"),
)

if not PG_CONFIG["password"]:
    print("❌ PG_PASSWORD not set.")
    sys.exit(1)

def get_counts(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM chunks;")
        chunk_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM openalex_works WHERE chunking_status != 'pending';")
        non_pending = cur.fetchone()[0]
    return chunk_count, non_pending

def main():
    conn = psycopg2.connect(**PG_CONFIG)
    chunk_count, non_pending = get_counts(conn)

    print(f"📊 Current state:")
    print(f"   • Chunks in table: {chunk_count}")
    print(f"   • Papers with chunking_status != 'pending': {non_pending}")

    confirm = input("\n⚠️  This will DELETE all chunks and reset chunking_status to 'pending'.\n"
                    "Type 'YES' to proceed: ")
    if confirm.strip().upper() != "YES":
        print("❌ Aborted.")
        return

    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE chunks;")
        cur.execute("UPDATE openalex_works SET chunking_status = 'pending';")
    conn.commit()
    conn.close()

    print("✅ All chunks deleted and chunking_status reset to 'pending'. Ready for re-chunking.")

if __name__ == "__main__":
    main()
