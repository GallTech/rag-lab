import os
import json
import requests
import psycopg2
import time
from urllib.parse import urlencode
from datetime import datetime

# === Config ===
CONFIG_PATH = "../config/openalex_config.json"
OUTPUT_DIR = os.path.expanduser("~/staging")
META_DIR = os.path.join(OUTPUT_DIR, "metadata")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")

DB_HOST = "192.168.0.11"
DB_PORT = 5432
DB_NAME = "raglab"
DB_USER = "mike"
DB_PASSWORD = os.getenv("PG_PASSWORD")

PER_PAGE = 50
DOWNLOAD_LIMIT = 100_000
RETRY_COUNT = 3
RETRY_DELAY = 5

BASE_URL = "https://api.openalex.org/works"
TABLE_NAME = "openalex_works"
TRUSTED_OA_DOMAINS = [
    "arxiv.org", "osf.io", "biorxiv.org", "medrxiv.org", "europepmc.org", "nih.gov/pmc"
]

os.makedirs(META_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# === Load config ===
with open(CONFIG_PATH) as f:
    config = json.load(f)

EMAIL = config["email"]
CONCEPT_IDS = ",".join([c["concept_id"] for c in config["topics"]])
DATE_FROM = config["from_date"]
DATE_TO = config["to_date"]

# === Connect to PostgreSQL ===
pg_conn = psycopg2.connect(
    host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
)
pg_cursor = pg_conn.cursor()

def already_downloaded(work_id: str) -> bool:
    pg_cursor.execute("SELECT 1 FROM openalex_works WHERE id = %s", (work_id,))
    return pg_cursor.fetchone() is not None

def build_url(cursor="*"):
    params = {
        "filter": f"concepts.id:{CONCEPT_IDS},open_access.is_oa:true,publication_date:{DATE_FROM}:{DATE_TO}",
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

def download_with_retries(url, path):
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            return True
        except Exception as e:
            print(f"❌ Retry {attempt} for {url}: {e}")
            time.sleep(RETRY_DELAY)
    return False

def download(work, pdf_url):
    work_id = work["id"]
    short_id = work_id.split("/")[-1]

    meta_path = os.path.join(META_DIR, f"{short_id}.json")
    pdf_path = os.path.join(PDF_DIR, f"{short_id}.pdf")

    with open(meta_path, "w") as f:
        json.dump(work, f, indent=2)

    if download_with_retries(pdf_url, pdf_path):
        print(f"✅ {short_id} downloaded")
        return True
    else:
        print(f"❌ {short_id} failed PDF download")
        return False

def main():
    cursor = "*"
    total = 0

    while total < DOWNLOAD_LIMIT:
        url = build_url(cursor)
        print(f"📡 Fetching: {url}")
        r = requests.get(url, timeout=60)
        if r.status_code == 403:
            print("❌ 403 Forbidden. Check email parameter or rate limits.")
            break
        r.raise_for_status()

        data = r.json()
        for work in data["results"]:
            work_id = work["id"]
            if already_downloaded(work_id):
                continue
            pdf_url = get_trusted_pdf_url(work)
            if not pdf_url:
                continue
            if download(work, pdf_url):
                total += 1
            if total >= DOWNLOAD_LIMIT:
                break

        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break

    print(f"\n✅ Finished. {total} items downloaded.")
    pg_conn.close()

if __name__ == "__main__":
    main()