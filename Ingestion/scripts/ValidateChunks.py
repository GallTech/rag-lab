import os
import psycopg2
from datetime import datetime

# === Config ===
PG_CONFIG = {
    "host": "192.168.0.11",
    "dbname": "raglab",
    "user": "mike",
    "password": os.getenv("PG_PASSWORD")
}

if not PG_CONFIG["password"]:
    raise RuntimeError("❌ PG_PASSWORD not set.")

def connect_pg():
    return psycopg2.connect(**PG_CONFIG)

def run_query(cur, label, sql):
    cur.execute(sql)
    count = cur.fetchone()[0]
    print(f"{label:<45} {count}")

def main():
    print(f"=== Chunk Audit Report ({datetime.utcnow().isoformat()}) ===\n")
    conn = connect_pg()
    cur = conn.cursor()

    # Total chunks
    run_query(cur, "Total chunks:", "SELECT COUNT(*) FROM chunks;")

    # Empty chunks
    run_query(cur, "Empty chunks:", "SELECT COUNT(*) FROM chunks WHERE length(trim(text)) = 0;")

    # Suspiciously short (<50 chars)
    run_query(cur, "Short chunks (<50 chars):", "SELECT COUNT(*) FROM chunks WHERE length(text) < 50;")

    # Suspiciously long (>2000 chars)
    run_query(cur, "Long chunks (>2000 chars):", "SELECT COUNT(*) FROM chunks WHERE length(text) > 2000;")

    # Works with < 2 chunks
    cur.execute("""
        SELECT COUNT(*) 
        FROM (
            SELECT work_id, COUNT(*) as c 
            FROM chunks 
            GROUP BY work_id 
            HAVING COUNT(*) < 2
        ) sub;
    """)
    print(f"{'Works with < 2 chunks:':<45} {cur.fetchone()[0]}")

    cur.close()
    conn.close()
    print("\n✅ Audit complete.")

if __name__ == "__main__":
    main()
