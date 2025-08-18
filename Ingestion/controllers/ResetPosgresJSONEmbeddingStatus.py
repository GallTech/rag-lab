#!/usr/bin/env python3
import os, psycopg2

PG_CONFIG = dict(host="192.168.0.11", dbname="raglab", user="mike", password=os.getenv("PG_PASSWORD"))
with psycopg2.connect(**PG_CONFIG) as conn, conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM chunks WHERE embedded = TRUE;")
    before = cur.fetchone()[0]
    print(f"🔧 Chunks with embedded=TRUE before: {before}")

    cur.execute("UPDATE chunks SET embedded = FALSE WHERE embedded = TRUE;")
    print(f"✅ Rows updated: {cur.rowcount}")

    cur.execute("""
        SELECT COUNT(*) AS total, 
               COUNT(*) FILTER (WHERE embedded) AS still_true
        FROM chunks;
    """)
    total, still_true = cur.fetchone()
    print(f"📊 Total chunks: {total} | embedded=TRUE after: {still_true}")
