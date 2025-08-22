#!/usr/bin/env python3
# Intra-paper clustering sanity for Qdrant (no /embed calls)
import os, random, requests, collections

QURL = os.getenv("QDRANT_URL", "http://192.168.0.11:6333")
COLL = os.getenv("QDRANT_COLLECTION", "openalex")

# Tuning knobs (env overrides welcome)
NUM_PAPERS     = int(os.getenv("NUM_PAPERS", "20"))   # distinct work_ids to test
MIN_CHUNKS     = int(os.getenv("MIN_CHUNKS", "5"))    # papers must have at least this many chunks present
SAMPLE_PER_P   = int(os.getenv("SAMPLE_PER_P", "5"))  # queries per paper
TOPK           = int(os.getenv("TOPK", "10"))         # neighbors to inspect
HNSW_EF        = int(os.getenv("HNSW_EF", "256"))

def qinfo():
    r = requests.get(f"{QURL}/collections/{COLL}", timeout=15)
    r.raise_for_status()
    return r.json()["result"]

def scroll_points(n=1000, with_vector=False, with_payload=True):
    out, page = [], None
    while True:
        need = n - len(out)
        if need <= 0:
            break
        body = {"limit": min(256, need), "with_vector": with_vector, "with_payload": with_payload}
        if page:
            body["page"] = page
        r = requests.post(f"{QURL}/collections/{COLL}/points/scroll", json=body, timeout=30)
        r.raise_for_status()
        j = r.json()["result"]
        out += j["points"]
        page = j.get("next_page_offset")
        if not page:
            break
    return out

def fetch_points(ids, with_vector=True, with_payload=True):
    r = requests.post(
        f"{QURL}/collections/{COLL}/points",
        json={"ids": ids, "with_vector": with_vector, "with_payload": with_payload},
        timeout=30
    )
    r.raise_for_status()
    got = r.json()["result"]
    # Normalize to dict by id (stringify ids for safety)
    return {str(p["id"]): p for p in got}

def search(vec, k=TOPK):
    r = requests.post(
        f"{QURL}/collections/{COLL}/points/search",
        json={
            "vector": vec,
            "limit": k,
            "params": {"hnsw_ef": HNSW_EF},
            "with_payload": True  # ensure payloads are returned
        },
        timeout=30
    )
    r.raise_for_status()
    return r.json()["result"]

def sample_papers():
    # First pass: scroll payloads (no vectors) to find work_ids with enough chunks
    pts = scroll_points(n=50000, with_vector=False, with_payload=True)
    groups = collections.defaultdict(list)
    for p in pts:
        payload = p.get("payload") or {}
        wid = payload.get("work_id")
        if wid is not None:
            groups[wid].append(p["id"])
    eligible = [wid for wid, ids in groups.items() if len(ids) >= MIN_CHUNKS]
    random.shuffle(eligible)
    chosen = eligible[:NUM_PAPERS]

    # Fetch vectors for chosen IDs
    paper_map = {}
    for wid in chosen:
        ids = groups[wid]
        random.shuffle(ids)
        pick = ids[:max(SAMPLE_PER_P, MIN_CHUNKS)]
        got = fetch_points(pick, with_vector=True, with_payload=True)
        paper_map[wid] = [got[str(i)] for i in pick if str(i) in got]
    return paper_map

def main():
    info = qinfo()
    print(f"Collection: {COLL}  points={info['points_count']}")
    papers = sample_papers()
    if not papers:
        print("No eligible papers found with enough chunks. Try lowering MIN_CHUNKS or increasing scroll size.")
        return

    total_queries = 0
    same_at_1 = 0
    same_at_k = 0
    mrr_sum = 0.0
    missing_payload_hits = 0

    for wid, points in papers.items():
        # Only query up to SAMPLE_PER_P for this paper
        random.shuffle(points)
        queries = points[:SAMPLE_PER_P]
        for p in queries:
            vec = p.get("vector")
            if not isinstance(vec, list):
                continue  # skip malformed
            res = search(vec, k=TOPK)
            total_queries += 1

            # Extract neighbor work_ids defensively
            neighbor_wids = []
            for h in res:
                payload = h.get("payload") or {}
                if not payload:
                    missing_payload_hits += 1
                neighbor_wids.append(payload.get("work_id"))

            # Count same-work neighbors (including self, if returned)
            same_flags = [1 if w == wid else 0 for w in neighbor_wids]

            same_at_1 += same_flags[0] if same_flags else 0
            same_at_k += sum(same_flags)

            # MRR@k for same-work_id (1/rank of first same-work hit)
            rr = 0.0
            for rank, flag in enumerate(same_flags, start=1):
                if flag:
                    rr = 1.0 / rank
                    break
            mrr_sum += rr

    if total_queries == 0:
        print("No queries executed.")
        return

    p_at_1 = same_at_1 / total_queries
    same_per_query = same_at_k / total_queries
    mrr_at_k = mrr_sum / total_queries

    print(f"Tested papers: {len(papers)}  queries: {total_queries}  topk={TOPK}")
    print(f"P@1 (same work_id at top-1): {p_at_1:.3f}")
    print(f"Avg same-work neighbors per query (out of {TOPK}): {same_per_query:.2f}")
    print(f"MRR@{TOPK} for same-work matches: {mrr_at_k:.3f}")
    if missing_payload_hits:
        print(f"ℹ️ Note: {missing_payload_hits} hits lacked payloads in results (legacy points or ingestion issue).")

    # Simple health hints (tune to your data/model)
    if p_at_1 < 0.5:
        print("⚠️ Low P@1 — chunks from the same paper aren’t clustering strongly at rank 1.")
    if same_per_query < TOPK * 0.4:
        print("⚠️ Few same-work neighbors in top-k — check chunking size/overlap or model consistency.")
    if mrr_at_k < 0.6:
        print("⚠️ Low MRR — related chunks are not ranking early. Consider auditing example papers.")

if __name__ == "__main__":
    main()
