import duckdb
import requests

# === Config ===
DB_PATH = "/mnt/duckdb/rag.duckdb"
TABLE_NAME = "openalex_works"
VOLUME_SERVER = "http://192.168.0.17:8080"  # Not the master
EXISTING_VOLUMES = range(1, 8)  # You can confirm these via /dir/status

# === 1. Wipe DuckDB ===
print("🧹 Deleting all rows from DuckDB...")
con = duckdb.connect(DB_PATH)
con.execute(f"DELETE FROM {TABLE_NAME};")
con.close()
print("✅ DuckDB cleared.")

# === 2. Delete volumes from SeaweedFS ===
print("🧹 Deleting SeaweedFS volumes...")

deleted = 0
failed = 0

for vid in EXISTING_VOLUMES:
    url = f"{VOLUME_SERVER}/admin/delete_volume?volume={vid}"
    try:
        r = requests.post(url, timeout=5)
        if r.status_code == 200:
            print(f"✅ Deleted volume {vid}")
            deleted += 1
        else:
            print(f"❌ Failed to delete volume {vid} ({r.status_code})")
            failed += 1
    except Exception as e:
        print(f"❌ Exception deleting volume {vid}: {e}")
        failed += 1

print(f"\n✅ {deleted} volumes deleted.")
if failed:
    print(f"⚠️ {failed} deletions failed.")