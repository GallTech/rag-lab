import os
import duckdb
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# === Config ===
PDF_DIR = os.path.expanduser("~/staging/pdfs")
DB_PATH = "/mnt/duckdb/rag.duckdb"
TABLE_NAME = "openalex_works"
SEAWEED_MASTER = "http://192.168.0.17:9333"
MAX_WORKERS = 4
ASSIGN_RETRIES = 5
ASSIGN_DELAY = 1.0  # seconds

# === Connect to DuckDB ===
con = duckdb.connect(DB_PATH)
con.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN IF NOT EXISTS pdf_fid TEXT")

# === Get already-uploaded IDs ===
existing = set(row[0] for row in con.execute(
    f"SELECT id FROM {TABLE_NAME} WHERE pdf_fid IS NOT NULL"
).fetchall())

# === Assign helper with retry ===
def get_fid_with_retry():
    for _ in range(ASSIGN_RETRIES):
        try:
            r = requests.get(f"{SEAWEED_MASTER}/dir/assign", params={"replication": "000"})
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(ASSIGN_DELAY)
    return None

# === Upload a single PDF ===
def upload_pdf(filename):
    paper_id = f"https://openalex.org/{os.path.splitext(filename)[0]}"
    file_path = os.path.join(PDF_DIR, filename)

    if paper_id in existing:
        return (paper_id, None, "already_uploaded")

    assign_data = get_fid_with_retry()
    if not assign_data or not assign_data.get("fid") or not assign_data.get("publicUrl"):
        return (paper_id, None, "assign_failed")

    fid = assign_data["fid"]
    public_url = assign_data["publicUrl"]

    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            r = requests.post(f"http://{public_url}/{fid}", files=files)
            r.raise_for_status()
    except Exception as e:
        return (paper_id, None, f"upload_failed: {e}")

    try:
        con.execute(f"UPDATE {TABLE_NAME} SET pdf_fid = ? WHERE id = ?", (fid, paper_id))
        return (paper_id, fid, "uploaded")
    except Exception as e:
        return (paper_id, None, f"db_update_failed: {e}")

# === Upload in parallel ===
results = []
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [
        executor.submit(upload_pdf, f)
        for f in os.listdir(PDF_DIR)
        if f.endswith(".pdf")
    ]
    for future in as_completed(futures):
        results.append(future.result())

# === Summary ===
uploaded = sum(1 for r in results if r[2] == "uploaded")
skipped = sum(1 for r in results if r[2] == "already_uploaded")
failed = [r for r in results if "failed" in r[2]]

print(f"\n✅ Upload complete")
print(f"  Uploaded: {uploaded}")
print(f"  Skipped (already in DB): {skipped}")
print(f"  Failed: {len(failed)}")

if failed:
    print("\n❌ Failures:")
    for paper_id, _, reason in failed:
        print(f"  - {paper_id}: {reason}")

con.close()