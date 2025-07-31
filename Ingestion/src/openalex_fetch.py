import os
import json
import requests
import duckdb
from urllib.parse import urlencode

# ==== CONFIG ====

CONFIG_PATH = os.path.expanduser("~/rag-lab/Ingestion/config/openalex_config.json")
OUTPUT_DIR = os.path.expanduser("~/staging")
META_DIR = os.path.join(OUTPUT_DIR, "metadata")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")
DB_PATH = "/mnt/duckdb/rag.duckdb"
TABLE_NAME = "openalex_works"

os.makedirs(META_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

EMAIL = CONFIG["email"]
TOPICS = CONFIG["topics"]
DATE_FROM = CONFIG["from_date"]
DATE_TO = CONFIG["to_date"]
PER_PAGE = CONFIG["per_page"]
CONCEPT_ID = TOPICS[0]["concept_id"]

BASE_URL = "https://api.openalex.org/works"

TRUSTED_OA_DOMAINS = [
    "arxiv.org", "osf.io", "biorxiv.org", "medrxiv.org", "europepmc.org", "nih.gov/pmc"
]

# ==== DB CONNECTION ====

con = duckdb.connect(DB_PATH)

def is_already_loaded(work_id: str) -> bool:
    result = con.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE id = ?", (work_id,)).fetchone()
    return result[0] > 0

# ==== HELPERS ====

def build_url(cursor="*"):
    params = {
        "filter": f"concepts.id:{CONCEPT_ID},from_publication_date:{DATE_FROM},to_publication_date:{DATE_TO},open_access.is_oa:true",
        "per_page": PER_PAGE,
        "cursor": cursor,
        "mailto": EMAIL
    }
    return f"{BASE_URL}?{urlencode(params)}"

def get_trusted_pdf_url(work):
    candidates = []
    best = work.get("best_oa_location")
    if best and best.get("pdf_url"):
        candidates.append(best["pdf_url"])
    for loc in work.get("locations", []):
        if loc.get("pdf_url"):
            candidates.append(loc["pdf_url"])
    for url in candidates:
        if any(domain in url for domain in TRUSTED_OA_DOMAINS):
            return url
    return None

def download_pdf_and_metadata(work, pdf_url):
    title_safe = "".join(c for c in work["title"] if c.isalnum() or c in (" ", "_", "-"))[:100]
    work_id = work["id"].split("/")[-1]

    if is_already_loaded(work["id"]):
        print(f"⏩ Skipped (already in DuckDB): {title_safe}")
        return

    meta_path = os.path.join(META_DIR, f"{work_id}.json")
    pdf_path = os.path.join(PDF_DIR, f"{work_id}.pdf")

    with open(meta_path, "w") as f:
        json.dump(work, f, indent=2)

    try:
        resp = requests.get(pdf_url, timeout=60)
        resp.raise_for_status()
        with open(pdf_path, "wb") as f:
            f.write(resp.content)
        print(f"✅ Downloaded: {title_safe}")
    except Exception as e:
        print(f"❌ Failed to download PDF for {title_safe}: {e}")

# ==== MAIN ====

def main():
    print(f"=== Starting OpenAlex download for concept {CONCEPT_ID} ===")
    cursor = "*"
    total_downloads = 0
    download_limit = 10_000

    while total_downloads < download_limit:
        url = build_url(cursor)
        print(f"\nFetching page (cursor={cursor}) ...")
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"🚫 HTTP error: {e}")
            break
        data = r.json()

        for work in data["results"]:
            if total_downloads >= download_limit:
                break

            pdf_url = get_trusted_pdf_url(work)
            if not pdf_url:
                continue

            download_pdf_and_metadata(work, pdf_url)
            total_downloads += 1

        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            print("No more pages.")
            break

    print(f"=== Done. Total downloaded: {total_downloads} ===")

if __name__ == "__main__":
    try:
        main()
    finally:
        con.close()