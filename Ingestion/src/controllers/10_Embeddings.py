#!/usr/bin/env python3
import os
import time
import uuid
import requests
import psycopg2
import psycopg2.extras

# === Config ===
PG_CONFIG = dict(
    host="192.168.0.11",
    dbname="raglab",
    user="mike",
    password=os.getenv("PG_PASSWORD"),
)
EMBED_ENDPOINT = "http://192.168.0.12:8000/embed"
QDRANT_URL = "http://192.168.0.11:6333"
QDRANT_COLLECTION = "openalex"

BATCH_SIZE = 1000         # total chunks to process per loop
EMBED_CHUNK_SIZE = 192    # per request to embed server (2× current size)
QDRANT_CHUNK_SIZE = 512   # per upsert to Qdrant
SLEEP_BETWEEN_BATCHES = 0 # seconds

if not PG_CONFIG["password"]:
    raise RuntimeError("❌ PG_PASSWORD not set.")

def get_conn():
    return psycopg2.connect(**PG_CONFIG)

def fetch_unembedded(limit):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id::text, work_id, text
            FROM chunks
            WHERE embedded = FALSE
            ORDER BY created_at
            LIMIT %s;
        """, (limit,))
        return cur.fetchall()

def mark_embedded(ids):
    with get_conn() as conn, conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """
            UPDATE chunks AS c
            SET embedded = TRUE
            FROM (VALUES %s) AS v(id)
            WHERE c.id = v.id::uuid;
            """,
            [(i,) for i in ids],
            template=None
        )
        conn.commit()

def embed_texts(texts):
    r = requests.post(EMBED_ENDPOINT, json={"texts": texts}, timeout=600)
    r.raise_for_status()
    data = r.json()
    return data.get("embeddings", data)

def upsert_points(points):
    r = requests.put(
        f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points",
        json={"points": points},
        timeout=60
    )
    r.raise_for_status()

def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]

def process_batch():
    rows = fetch_unembedded(BATCH_SIZE)
    if not rows:
        return 0

    print(f"📦 Fetched {len(rows)} chunks from Postgres...")
    start_time = time.time()

    ids, work_ids, texts = zip(*rows)
    vectors = []

    count = 0
    for sub in chunked(list(texts), EMBED_CHUNK_SIZE):
        emb = embed_texts(sub)
        vectors.extend(emb)
        count += len(sub)
        print(f"   Embedded {count}/{len(rows)} chunks...")

    points = []
    for i, vec in enumerate(vectors):
        points.append({
            "id": ids[i],
            "vector": vec,
            "payload": {
                "work_id": work_ids[i],
                "chunk_id": ids[i],
                "source": "openalex",
            },
        })

    for sub in chunked(points, QDRANT_CHUNK_SIZE):
        upsert_points(sub)

    mark_embedded(ids)

    elapsed = time.time() - start_time
    print(f"✅ Done: {len(rows)} chunks embedded and uploaded in {elapsed:.2f} sec")
    print(f"⚡ {len(rows)/elapsed:.2f} chunks/sec")

    return len(rows)

def main():
    total_processed = 0
    while True:
        processed = process_batch()
        if processed == 0:
            print("🎉 All chunks embedded.")
            break
        total_processed += processed
        print(f"📊 Total processed so far: {total_processed}")
        time.sleep(SLEEP_BETWEEN_BATCHES)

if __name__ == "__main__":
    main()