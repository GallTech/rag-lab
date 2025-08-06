import os
import json
import requests
import psycopg2
import time
from urllib.parse import quote_plus, urlparse

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
RETRY_COUNT = 1
RETRY_DELAY = 5

BASE_URL = "https://api.openalex.org/works"
TABLE_NAME = "openalex_works"
TRUSTED_OA_DOMAINS = [
    "arxiv.org", "osf.io", "biorxiv.org", "medrxiv.org", "europepmc.org", "nih.gov/pmc"
]

BLOCKED_DOMAINS = [
    "academic.oup.com",
    "dl.acm.org",
    "repositorio.unal.edu.co",
    "rss.onlinelibrary.wiley.com",
    "research.rug.nl",
    "discovery.ucl.ac.uk",
    "deepblue.lib.umich.edu",
    "onlinelibrary.wiley.com",
    "www.tandfonline.com",
    "saberesepraticas.cenpec.org.br",
    "www.nature.com",
    "lirias.kuleuven.be",
    "www.thelancet.com",
    "eprints.whiterose.ac.uk",
    "cris.maastrichtuniversity.nl",
    "eprints.qut.edu.au",
    "advances.sciencemag.org",
    "direct.mit.edu",
    "zenodo.org",
    "ahajournals.org",
    "scans.hebis.de",
    "www.zora.uzh.ch",
    "www.biorxiv.org",
    "www.sciencedirect.com",
    "nsuworks.nova.edu"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

os.makedirs(META_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# === Load config ===
with open(CONFIG_PATH) as f:
    config = json.load(f)

EMAIL = config["email"]
CONCEPT_IDS = ",".join([c["concept_id"] for c in config["topics"]])

# === Connect to PostgreSQL ===
pg_conn = psycopg2.connect(
    host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
)
pg_cursor = pg_conn.cursor()

def already_downloaded(work_id: str) -> bool:
    pg_cursor.execute("SELECT 1 FROM openalex_works WHERE id = %s", (work_id,))
    return pg_cursor.fetchone() is not None

def build_url(cursor="*"):
    filter_str = f"concepts.id:{CONCEPT_IDS},open_access.is_oa:true"
    params = {
        "filter": filter_str,
        "per_page": PER_PAGE,
        "cursor": cursor,
        "mailto": EMAIL
    }
    query = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items() if k != "filter")
    return f"{BASE_URL}?filter={filter_str}&{query}"

def get_pdf_url(work):
    candidates = []
    best = work.get("best_oa_location")
    if best and best.get("pdf_url"):
        candidates.append(best["pdf_url"])
    for loc in work.get("locations", []):
        if loc.get("pdf_url"):
            candidates.append(loc["pdf_url"])

    for url in candidates:
        domain = urlparse(url).netloc
        if domain in BLOCKED_DOMAINS:
            print(f"⛔ Skipping blocked domain: {domain} → {url}")
            continue
        if any(trusted in url for trusted in TRUSTED_OA_DOMAINS):
            return url
        return url  # fallback if no trust check required

    return None

def download(work, pdf_url):
    work_id = work["id"]
    short_id = work_id.split("/")[-1]

    meta_path = os.path.join(META_DIR, f"{short_id}.json")
    pdf_path = os.path.join(PDF_DIR, f"{short_id}.pdf")

    with open(meta_path, "w") as f:
        json.dump(work, f, indent=2)

    for attempt in range(RETRY_COUNT):
        try:
            r = requests.get(pdf_url, timeout=60, headers=HEADERS)
            r.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(r.content)
            print(f"✅ {short_id} downloaded")
            return True
        except Exception as e:
            print(f"❌ Retry {attempt+1} for {short_id}: {e}")
            time.sleep(RETRY_DELAY)
    print(f"❌ {short_id} failed PDF download")
    return False

def main():
    cursor = "*"
    total = 0

    while total < DOWNLOAD_LIMIT:
        url = build_url(cursor)
        print(f"📡 Fetching: {url}")
        r = requests.get(url, timeout=60, headers=HEADERS)

        if r.status_code == 403 or r.status_code == 400:
            print(f"❌ HTTP {r.status_code}. Full response:")
            print(r.text)
            break

        r.raise_for_status()
        data = r.json()

        for work in data["results"]:
            work_id = work["id"]
            if already_downloaded(work_id):
                continue
            pdf_url = get_pdf_url(work)
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