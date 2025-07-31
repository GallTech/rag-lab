import duckdb
import json
from collections import Counter

# === Config ===
DB_PATH = "/mnt/duckdb/rag.duckdb"
TABLE_NAME = "openalex_works"
OUTPUT_FILE = "topic_counts.txt"

# === Connect
con = duckdb.connect(DB_PATH)

# === Fetch all topics
rows = con.execute(f"SELECT topics FROM {TABLE_NAME} WHERE topics IS NOT NULL").fetchall()

# === Count topics
counter = Counter()

for (topics_json,) in rows:
    try:
        topic_list = json.loads(topics_json)
        for topic in topic_list:
            name = topic.get("name") or topic.get("display_name")
            if name:
                counter[name] += 1
    except Exception:
        continue  # skip malformed rows

# === Output
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for name, count in counter.most_common():
        f.write(f"{name}: {count}\n")

print(f"✅ Topic counts written to {OUTPUT_FILE}")