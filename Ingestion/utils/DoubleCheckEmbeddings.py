import psycopg2
import os

PG_CONFIG = {
    "host": "192.168.0.11",
    "dbname": "raglab",
    "user": "mike",
    "password": os.getenv("PG_PASSWORD")
}

if not PG_CONFIG["password"]:
    raise RuntimeError("PG_PASSWORD not set.")

def check_embedding_completion():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    # Total papers that have been chunked
    cur.execute("""
        SELECT COUNT(DISTINCT work_id)
        FROM chunks;
    """)
    total_chunked = cur.fetchone()[0]

    # Papers fully embedded (all chunks embedded = TRUE)
    cur.execute("""
        SELECT COUNT(DISTINCT work_id)
        FROM chunks
        GROUP BY work_id
        HAVING BOOL_AND(embedded = TRUE);
    """)
    fully_embedded = len(cur.fetchall())

    # Papers partially embedded
    partial_embedded = total_chunked - fully_embedded

    cur.close()
    conn.close()

    print(f"📑 Total chunked papers: {total_chunked}")
    print(f"✅ Fully embedded papers: {fully_embedded}")
    print(f"⚠️ Not yet embedded papers: {partial_embedded}")
    print()

    if partial_embedded == 0:
        print("🎯 All chunked papers are fully embedded — ready to use!")
    else:
        print("⚠️ Not all papers are fully embedded. Retrieval may miss content for partial ones.")

if __name__ == "__main__":
    check_embedding_completion()
