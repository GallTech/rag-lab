#!/usr/bin/env python3
# Qdrant-only sanity: no calls to /embed
import requests, os, random

QURL = os.getenv("QDRANT_URL", "http://192.168.0.11:6333")
COLL = os.getenv("QDRANT_COLLECTION", "openalex")
SAMPLE = int(os.getenv("SAMPLE", "100"))   # number of points to test
TOPK = 3                                   # require self to be in top-1 (or relax to top-3)
HNSW_EF = 256

def qinfo():
    r = requests.get(f"{QURL}/collections/{COLL}", timeout=15)
    r.raise_for_status()
    return r.json()["result"]

def scroll_with_vectors(n):
    out, page = [], None
    while len(out) < n:
        body = {"limit": min(64, n - len(out)), "with_vector": True, "with_payload": True}
        if page: body["page"] = page
        r = requests.post(f"{QURL}/collections/{COLL}/points/scroll", json=body, timeout=30)
        r.raise_for_status()
        j = r.json()["result"]
        out += j["points"]
        page = j.get("next_page_offset")
        if not page: break
    return out[:n]

def search(vec, k=TOPK):
    r = requests.post(
        f"{QURL}/collections/{COLL}/points/search",
        json={"vector": vec, "limit": k, "params": {"hnsw_ef": HNSW_EF}},
        timeout=30
    )
    r.raise_for_status()
    return r.json()["result"]

def main():
    info = qinfo()
    total_points = info["points_count"]
    vec_param = info["config"]["params"]["vectors"]
    dim = vec_param["size"] if "size" in vec_param else list(vec_param.values())[0]["size"]
    print(f"Collection: {COLL}  points={total_points}  dim={dim}")

    pts = scroll_with_vectors(min(SAMPLE, total_points))
    if not pts:
        print("No points to sample. Exiting.")
        return

    # Basic payload + vector checks
    bad_payload = 0
    bad_vector = 0
    for p in pts:
        if "payload" not in p or "work_id" not in p["payload"] or "chunk_id" not in p["payload"]:
            bad_payload += 1
        v = p.get("vector")
        if not isinstance(v, list) or len(v) != dim:
            bad_vector += 1

    if bad_payload or bad_vector:
        print(f"⚠️ Payload issues: {bad_payload} / {len(pts)}   Vector shape issues: {bad_vector} / {len(pts)}")

    # Self-nearest check (no /embed call)
    fails = 0
    sims = []
    for p in pts:
        res = search(p["vector"])
        hit_ids = [h["id"] for h in res]
        # For cosine distance, Qdrant returns similarity as "score" (closer to 1 better)
        sims.append(res[0]["score"])
        if p["id"] != hit_ids[0]:
            fails += 1

    avg_sim = sum(sims) / len(sims)
    print(f"Self-nearest failures (top-1): {fails}/{len(pts)}")
    print(f"Avg top-1 similarity: {avg_sim:.4f}  (cosine ~1.0 is best)")

    # Optional: quick count parity versus DB (only if you want)
    # Uncomment and set PG env vars if you want this:
    # import psycopg2
    # PG = dict(host=os.getenv("PG_HOST","192.168.0.11"), dbname=os.getenv("PG_DB","raglab"),
    #           user=os.getenv("PG_USER","mike"), password=os.getenv("PG_PASSWORD"))
    # with psycopg2.connect(**PG) as c, c.cursor() as cur:
    #     cur.execute("SELECT COUNT(*) FROM chunks WHERE embedded=TRUE")
    #     dbcount = cur.fetchone()[0]
    # print(f"Count parity: Qdrant={total_points}  DB={dbcount}  delta={total_points - dbcount}")

if __name__ == "__main__":
    main()
