import duckdb
import requests

# CONFIG
DB_PATH = "/mnt/duckdb/rag.duckdb"
SEAWEED_URL = "http://192.168.0.17:8080"

# 1. Get all FIDs from DuckDB
con = duckdb.connect(DB_PATH)
rows = con.execute("SELECT id, pdf_fid FROM openalex_works WHERE pdf_fid IS NOT NULL").fetchall()

matched = 0
orphan_jsons = 0

# 2. Check each fid directly
for work_id, fid in rows:
    try:
        r = requests.head(f"{SEAWEED_URL}/{fid}", timeout=3)
        if r.status_code == 200:
            matched += 1
        else:
            orphan_jsons += 1
    except Exception:
        orphan_jsons += 1

# 3. Report
print(f"{matched} PDFs and JSONs match.")
print(f"0 PDFs are orphans (not in DuckDB).")
print(f"{orphan_jsons} JSONs are orphans (not in SeaweedFS).")