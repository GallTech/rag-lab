import os
import json
import requests
import psycopg2
import time
from datetime import datetime
from urllib.parse import quote_plus, urlparse
from urllib.parse import urlencode

# === Config ===
CONFIG_PATH = "../../config/openalex_config.json"
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

# === Logging ===
LOG_DIR = "/home/mike/rag-lab/Ingestion/src/logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = os.path.join(LOG_DIR, f"openalex_download_{log_stamp}.csv")

os.makedirs(META_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# === Load config ===
with open(CONFIG_PATH) as f:
    config = json.load(f)

EMAIL = config["email"]
CONCEPT_IDS = ",".join([c["concept_id"] for c in config["topics"]])

# === Publication date range filters from config (ONLY) ===
FROM_DATE = config.get("from_date")  # e.g. "2024-01-01"
TO_DATE   = config.get("to_date")    # e.g. "2024-07-01"

# === Connect to PostgreSQL ===
pg_conn = psycopg2.connect(
    host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
)
pg_cursor = pg_conn.cursor()

def already_downloaded(work_id: str) -> bool:
    pg_cursor.execute("SELECT 1 FROM openalex_works WHERE id = %s", (work_id,))
    return pg_cursor.fetchone() is not None

def build_url(cursor="*"):
    # Get the first topic's IDs (assuming one topic in config)
    topic = config["topics"][0]
    
    filter_parts = [
        f"concepts.id:{topic['concept_id']}",
        f"primary_topic.id:{topic['primary_topic_id']}",
        f"type:{config.get('type_filter', 'article')}",
        "open_access.is_oa:true"
    ]
    
    filter_str = ",".join(filter_parts)
    
    params = {
        "filter": filter_str,
        "per_page": config.get("per_page", 50),
        "cursor": cursor,
        "mailto": config["email"]
    }
    return f"{BASE_URL}?{urlencode(params)}"


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
    # init log file (two columns: filename, publication_date) + filter header
    with open(LOG_PATH, "w") as lf:
        lf.write(f"# filter from_publication_date={FROM_DATE},to_publication_date={TO_DATE}\n")
        lf.write("filename,publication_date\n")

    cursor = "*"
    total = 0
    out_of_range = 0  # sanity check for publication_date

    while total < DOWNLOAD_LIMIT:
        url = build_url(cursor)
        print(f"📡 Fetching: {url}")
        r = requests.get(url, timeout=60, headers=HEADERS)

        if r.status_code in (403, 400):
            print(f"❌ HTTP {r.status_code}. Full response:")
            print(r.text)
            break

        r.raise_for_status()
        data = r.json()

        for work in data.get("results", []):
            work_id = work["id"]
            if already_downloaded(work_id):
                continue

            pub_date = work.get("publication_date", "")

            # sanity check: pub_date must be within requested window
            if pub_date:
                if FROM_DATE and pub_date < FROM_DATE:
                    out_of_range += 1
                if TO_DATE and pub_date > TO_DATE:
                    out_of_range += 1

            pdf_url = get_pdf_url(work)
            if not pdf_url:
                continue

            if download(work, pdf_url):
                short_id = work_id.split("/")[-1]
                # append to log (filename, publication_date)
                with open(LOG_PATH, "a") as lf:
                    lf.write(f"{short_id}.pdf,{pub_date}\n")
                total += 1

            if total >= DOWNLOAD_LIMIT:
                break

        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break

    print(f"\n✅ Finished. {total} items downloaded.")
    if out_of_range:
        print(f"⚠️  {out_of_range} results had publication_date outside the requested window "
              f"(unexpected; logged for visibility).")
    print(f"📝 Log written to: {LOG_PATH}")
    pg_conn.close()

if __name__ == "__main__":
    main()