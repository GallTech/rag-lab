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
EMBED_ENDPOINT = os.getenv("EMBED_ENDPOINT", "http://lab-1-embed01:8000/embed")
QDRANT_URL = "http://192.168.0.11:6333"
QDRANT_COLLECTION = "openalex"

BATCH_SIZE = 1000         # total chunks to process per loop
EMBED_CHUNK_SIZE = 256    # per request to embed server
QDRANT_CHUNK_SIZE = 512   # per upsert to Qdrant
SLEEP_BETWEEN_BATCHES = 0 # seconds

# If the existing collection has a different vector size, should we drop & recreate?
QDRANT_RECREATE_ON_SIZE_MISMATCH = False

if not PG_CONFIG["password"]:
    raise RuntimeError("❌ PG_PASSWORD not set.")

# === ADDED: lightweight retry helper ===
def retry(fn, *, tries=5, delay=2, backoff=2, exceptions=(Exception,)):
    def _wrapped(*a, **kw):
        t, d = tries, delay
        while True:
            try:
                return fn(*a, **kw)
            except exceptions as e:
                t -= 1
                if t <= 0:
                    raise
                time.sleep(d)
                d *= backoff
    return _wrapped

# === DB helpers ===
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
    if not ids:
        return
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

# === Embedding & Qdrant helpers ===
@retry   
def embed_texts(texts):
    r = requests.post(EMBED_ENDPOINT, json={"texts": texts}, timeout=600)
    r.raise_for_status()
    data = r.json()
    # Accept both batch {vectors:[...]} and single {embedding:[...]}
    if isinstance(data, dict) and "vectors" in data:
        return data["vectors"]
    if isinstance(data, dict) and "embedding" in data:
        return [data["embedding"]]
    raise ValueError(f"Unexpected embed response keys: {list(data)[:5]}")
def ensure_collection(vector_size):
    """Ensure Qdrant collection exists with the given vector size."""
    base = f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}"
    r = requests.get(base, timeout=10)
    if r.status_code == 200:
        info = r.json().get("result", {})
        current_size = None
        vectors_param = info.get("config", {}).get("params", {}).get("vectors")
        if isinstance(vectors_param, dict) and "size" in vectors_param:
            current_size = vectors_param.get("size")
        elif isinstance(vectors_param, dict):
            for _, v in vectors_param.items():
                if isinstance(v, dict) and "size" in v:
                    current_size = v["size"]
                    break
        if current_size is not None and current_size != vector_size:
            msg = (f"⚠️  Collection '{QDRANT_COLLECTION}' exists with size={current_size}, "
                   f"but embeddings are size={vector_size}.")
            if QDRANT_RECREATE_ON_SIZE_MISMATCH:
                print(msg + " Recreating collection...")
                rd = requests.delete(base, timeout=30)
                rd.raise_for_status()
                _create_collection(base, vector_size)
                return
            else:
                raise RuntimeError(msg + " Set QDRANT_RECREATE_ON_SIZE_MISMATCH=True to auto-fix.")
        return
    if r.status_code != 404:
        r.raise_for_status()
    _create_collection(base, vector_size)

def _create_collection(base_url, vector_size):
    create_payload = {
        "vectors": {
            "size": vector_size,
            "distance": "Cosine"
        }
    }
    r = requests.put(base_url, json=create_payload, timeout=30)
    r.raise_for_status()
    print(f"🆕 Created Qdrant collection '{QDRANT_COLLECTION}' with size={vector_size}, distance=Cosine")

@retry  # ADDED
def upsert_points(points):
    # ADDED: ?wait=true ensures write durability before we mark embedded
    r = requests.put(
        f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points?wait=true",
        json={"points": points},
        timeout=120
    )
    r.raise_for_status()

def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]

# === Core processing ===
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

    # ADDED: sanity check
    if len(vectors) != len(rows):
        raise RuntimeError(f"Embedding count mismatch: got {len(vectors)} for {len(rows)} inputs")

    # Ensure collection with the correct vector size (infer from first vector)
    vec_size = len(vectors[0])
    ensure_collection(vec_size)

    # Build points (same order as inputs)
    points = []
    for i, vec in enumerate(vectors):
        points.append({
            "id": ids[i],     # UUID string is fine
            "vector": vec,    # single unnamed vector
            "payload": {
                "work_id": work_ids[i],
                "chunk_id": ids[i],
                "source": "openalex",
            },
        })

    # Upsert in chunks (wait=true inside upsert_points); only mark after all succeed
    sent = 0
    for sub in chunked(points, QDRANT_CHUNK_SIZE):
        upsert_points(sub)
        sent += len(sub)
        if sent % 1000 == 0 or sent == len(points):
            print(f"   Uploaded {sent}/{len(points)} to Qdrant...")

    # Only now mark embedded
    mark_embedded(ids)

    elapsed = time.time() - start_time
    print(f"✅ Done: {len(rows)} chunks embedded and uploaded in {elapsed:.2f} sec")
    if elapsed > 0:
        rate = len(rows)/elapsed
        print(f"⚡ {rate:.2f} chunks/sec")
    return len(rows)

def main():
    try:
        probe_vec = embed_texts(["probe"])[0]
        ensure_collection(len(probe_vec))
        print(f"🧪 Embed/vector-size probe OK: dim={len(probe_vec)}")
    except Exception as e:
        raise RuntimeError(f"Failed startup probe/ensure_collection: {e}")

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
