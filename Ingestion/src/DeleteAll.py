import duckdb
import requests

# === Config ===
DB_PATH = "/mnt/duckdb/rag.duckdb"
TABLE_NAME = "openalex_works"
SEAWEED_MASTER = "http://192.168.0.17:9333"
SEAWEED_VOLUME_PORT = 8080
VOLUME_RANGE = range(1, 101)  # Adjust if needed

# === 1. Wipe DuckDB ===
print("🧹 Deleting rows from DuckDB...")
con = duckdb.connect(DB_PATH)
con.execute(f"DELETE FROM {TABLE_NAME};")
con.close()
print("✅ DuckDB cleared.")

# === 2. Wipe SeaweedFS Volumes ===
print("🧹 Deleting all PDF files from SeaweedFS...")

deleted = 0
errors = 0

for vid in VOLUME_RANGE:
    try:
        index_url = f"http://192.168.0.17:{SEAWEED_VOLUME_PORT}/?volumeId={vid}"
        res = requests.get(index_url, timeout=5)
        if not res.ok or "html" not in res.text:
            continue

        for line in res.text.splitlines():
            if ".pdf" in line:
                fid = line.split()[0].split(".pdf")[0]
                delete_url = f"http://192.168.0.17:{SEAWEED_VOLUME_PORT}/{fid}"
                del_res = requests.delete(delete_url)
                if del_res.status_code == 200:
                    deleted += 1
                else:
                    errors += 1

    except Exception as e:
        continue

print(f"✅ SeaweedFS: {deleted} files deleted.")
if errors > 0:
    print(f"⚠️ {errors} deletions failed.")