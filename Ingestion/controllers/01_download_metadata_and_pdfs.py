import os
import json
import requests
import psycopg2
import time
from datetime import datetime
from urllib.parse import urlencode, urlparse

# === Config Paths ===
CONFIG_PATH = "/home/mike/rag-lab/Ingestion/config/openalex_config.json"
OUTPUT_DIR = os.path.expanduser("~/staging")
META_DIR = os.path.join(OUTPUT_DIR, "metadata")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")

# === Database Config ===
DB_HOST = "192.168.0.11"
DB_PORT = 5432
DB_NAME = "raglab"
DB_USER = "mike"
DB_PASSWORD = os.getenv("PG_PASSWORD")

# === API Config ===
BASE_URL = "https://api.openalex.org/works"
PER_PAGE = 50
DOWNLOAD_LIMIT = 100_000
RETRY_COUNT = 1
RETRY_DELAY = 1

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

# === Blocklist for PDF hosts ===
BLOCKED_DOMAINS = []
# Normalize and support subdomain matches: host == entry OR host endswith("." + entry_wo_www)
_BLOCKED_SUFFIXES = {d.lower().lstrip(".").removeprefix("www.") for d in BLOCKED_DOMAINS}
_BLOCKED_EXACT = {d.lower().lstrip(".") for d in BLOCKED_DOMAINS}

def is_blocked(url: str) -> bool:
    """Return True if URL host is in blocklist or is a subdomain of a blocked domain."""
    try:
        host = urlparse(url).netloc.split(":")[0].lower()
        host_wo_www = host.removeprefix("www.")
        if host in _BLOCKED_EXACT or host_wo_www in _BLOCKED_EXACT:
            return True
        return any(
            host == suf or host_wo_www == suf or host.endswith("." + suf)
            for suf in _BLOCKED_SUFFIXES
        )
    except Exception:
        return False

# === Setup Directories & Logging ===
os.makedirs(META_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)
LOG_DIR = "/home/mike/rag-lab/Ingestion/src/logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = os.path.join(LOG_DIR, f"openalex_download_{log_stamp}.csv")

# === Load and Validate Config ===
try:
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    if not all(k in config for k in ["email", "filters"]):
        raise ValueError("Config missing required fields (email or filters)")

    if not isinstance(config["filters"].get("concepts", []), list):
        raise ValueError("filters.concepts must be an array")

    EMAIL = config["email"]
    FILTERS = config["filters"]

except Exception as e:
    print(f"❌ Config error: {str(e)}")
    raise SystemExit(1)

# === Database Connection ===
try:
    pg_conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER,
        password=DB_PASSWORD
    )
    pg_cursor = pg_conn.cursor()
except Exception as e:
    print(f"❌ Database connection failed: {str(e)}")
    raise SystemExit(1)

def already_downloaded(work_id: str) -> bool:
    try:
        pg_cursor.execute("SELECT 1 FROM openalex_works WHERE id = %s", (work_id,))
        return pg_cursor.fetchone() is not None
    except Exception as e:
        print(f"⚠️ Database query failed: {str(e)}")
        return False

def build_url(cursor="*"):
    filter_parts = []

    # Handle concepts
    if concepts := FILTERS.get("concepts"):
        concept_filters = [f"concepts.id:{c}" for c in concepts]
        filter_parts.append("|".join(concept_filters))

    # Handle primary topics
    if primary_topics := FILTERS.get("primary_topics"):
        primary_filters = [f"primary_topic.id:{p}" for p in primary_topics]
        filter_parts.append("|".join(primary_filters))

    # Required filters
    filter_parts.extend([
        f"type:{FILTERS.get('type', 'article')}",
        f"open_access.is_oa:{str(FILTERS.get('open_access', True)).lower()}",
    ])

    # Date filters
    if from_date := FILTERS.get("from_date"):
        filter_parts.append(f"from_publication_date:{from_date}")
    if to_date := FILTERS.get("to_date"):
        filter_parts.append(f"to_publication_date:{to_date}")

    params = {
        "filter": ",".join(filter_parts),
        "per_page": config.get("per_page", PER_PAGE),
        "cursor": cursor,
        "mailto": EMAIL,
    }
    return f"{BASE_URL}?{urlencode(params)}"

def get_pdf_url(work):
    """Return first allowed PDF URL from OA locations, skipping blocked hosts."""
    locations = []
    if work.get("best_oa_location"):
        locations.append(work["best_oa_location"])
    locations.extend(work.get("locations", []))

    for loc in locations:
        if not loc:
            continue
        url = loc.get("pdf_url")
        if not url:
            continue
        if is_blocked(url):
            print(f"⛔ Blocked host for {work.get('id','?')}: {url}")
            continue
        return url
    return None

def download_paper(work):
    work_id = work["id"]
    short_id = work_id.split("/")[-1]
    pdf_url = get_pdf_url(work)

    if not pdf_url or is_blocked(pdf_url):
        print(f"⚠️ Skipping (blocked/no PDF): {short_id}")
        return False

    meta_path = os.path.join(META_DIR, f"{short_id}.json")
    pdf_path = os.path.join(PDF_DIR, f"{short_id}.pdf")

    try:
        # Save metadata
        with open(meta_path, "w") as f:
            json.dump(work, f, indent=2)

        # Download PDF with retries
        for attempt in range(RETRY_COUNT + 1):
            try:
                resp = requests.get(pdf_url, headers=HEADERS, timeout=30)
                resp.raise_for_status()
                with open(pdf_path, "wb") as f:
                    f.write(resp.content)
                print(f"✅ Downloaded {short_id}")
                return True
            except Exception as e:
                if attempt < RETRY_COUNT:
                    print(f"❌ Download error ({short_id}), retry {attempt+1}/{RETRY_COUNT}: {e}")
                    time.sleep(RETRY_DELAY)
                    continue
                print(f"❌ Failed to download {short_id}: {e}")
                return False
    except Exception as e:
        print(f"❌ File operation failed for {short_id}: {e}")
        return False

def main():
    # Initialize log
    with open(LOG_PATH, "w") as f:
        f.write("filename,publication_date,download_time,primary_topic_id,primary_topic_name\n")

    total_downloaded = 0
    cursor = "*"

    try:
        while total_downloaded < DOWNLOAD_LIMIT:
            url = build_url(cursor)
            print(f"🔍 Fetching: {url}")

            try:
                response = requests.get(url, headers=HEADERS, timeout=60)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                print(f"❌ API request failed: {e}")
                break

            results = data.get("results", [])
            if not results:
                break

            for work in results:
                if total_downloaded >= DOWNLOAD_LIMIT:
                    break

                if already_downloaded(work["id"]):
                    continue

                if download_paper(work):
                    pt = work.get("primary_topic") or {}
                    pt_id = pt.get("id", "")
                    pt_name = pt.get("display_name", "")
                    with open(LOG_PATH, "a") as f:
                        f.write(
                            f"{work['id'].split('/')[-1]}.pdf,"
                            f"{work.get('publication_date', '')},"
                            f"{datetime.now().isoformat()},"
                            f"{pt_id},{pt_name}\n"
                        )
                    total_downloaded += 1

            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break
    finally:
        pg_conn.close()

    print(f"\n🎉 Finished. Downloaded {total_downloaded} papers.")
    print(f"📊 Log saved to: {LOG_PATH}")

if __name__ == "__main__":
    main()