#!/usr/bin/env python3
import requests
import argparse

def count_distinct_work_ids(qdrant_url, collection, batch_size=1000):
    unique_ids = set()
    scroll_payload = {
        "limit": batch_size,
        "with_payload": True
    }
    next_page = None

    while True:
        if next_page:
            scroll_payload["offset"] = next_page
        r = requests.post(f"{qdrant_url}/collections/{collection}/points/scroll",
                          json=scroll_payload, timeout=30)
        r.raise_for_status()
        data = r.json()["result"]

        for point in data["points"]:
            work_id = point.get("payload", {}).get("work_id")
            if work_id:
                unique_ids.add(work_id)

        next_page = data.get("next_page_offset")
        if not next_page:
            break

    return len(unique_ids)

def main():
    parser = argparse.ArgumentParser(description="Count distinct PDFs (work_ids) in Qdrant collection.")
    parser.add_argument("--host", default="http://192.168.0.11:6333", help="Qdrant host:port")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--batch-size", type=int, default=1000, help="Scroll batch size")
    args = parser.parse_args()

    total = count_distinct_work_ids(args.host, args.collection, args.batch_size)
    print(f"📄 Collection '{args.collection}' contains embeddings for {total} distinct PDFs.")

if __name__ == "__main__":
    main()
