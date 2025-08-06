import os
import psycopg2

PG_CONFIG = {
    "host": "192.168.0.11",
    "dbname": "raglab",
    "user": "mike",
    "password": os.getenv("PG_PASSWORD")
}

ALTER_SQL = """
ALTER TABLE chunks
  ADD COLUMN IF NOT EXISTS embedding_status TEXT DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS embedding_attempts INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS last_embedding_attempt TIMESTAMP,
  ADD COLUMN IF NOT EXISTS error_message TEXT;
"""

def apply_migration():
    print("🔄 Applying schema migration...")
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    cur.execute(ALTER_SQL)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Migration complete.")

if __name__ == "__main__":
    apply_migration()