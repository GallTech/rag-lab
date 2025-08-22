#!/usr/bin/env python3
import os, sys, json, time, argparse
import requests, psycopg2
from datetime import datetime
from urllib.parse import urlencode, urlparse

# === Config Paths ===
CONFIG_PATH = "/home/mike/rag-lab/Ingestion/config/openalex_config.json"
OUTPUT_DIR = os.path.expanduser("~/staging")
META_DIR = os.path.join(OUTPUT_DIR, "metadata")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")

# === Database Config ===
DB_HOST, DB_PORT, DB_NAME, DB_USER = "192.168.0.11", 5432, "raglab", "mike"
DB_PASSWORD = os.getenv("PG_PASSWORD")

# === API Config ===
BASE_URL = "https://api.openalex.org/works"
PER_PAGE = 50
DOWNLOAD_LIMIT = 100_000
RETRY_COUNT = 1
RETRY_DELAY = 1

HEADERS = {"User-Agent": "Mozilla/5.0 (Linux; IngestionBot)", "Accept": "application/json"}

# === Blocklist (optional) ===
BLOCKED_DOMAINS = []
_BLOCKED_SUFFIXES = {d.lower().lstrip(".").removeprefix("www.") for d in BLOCKED_DOMAINS}
_BLOCKED_EXACT = {d.lower().lstrip(".") for d in BLOCKED_DOMAINS}

def is_blocked(url: str) -> bool:
    try:
        host = urlparse(url).netloc.split(":")[0].lower()
        host_wo_www = host.removeprefix("www.")
        if host in _BLOCKED_EXACT or host_wo_www in _BLOCKED_EXACT:
            return True
        return any(host == suf or host_wo_www == suf or host.endswith("." + suf) for suf in _BLOCKED_SUFFIXES)
    except Exception:
        return False

# === Setup Dirs & Log ===
os.makedirs(META_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)
LOG_DIR = "/home/mike/rag-lab/Ingestion/src/logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = os.path.join(LOG_DIR, f"openalex_download_{log_stamp}.csv")

# === Load Config ===
try:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    if not all(k in config for k in ["email", "filters"]):
        raise ValueError("Config missing required fields (email or filters)")
    EMAIL = config["email"]
    FILTERS = config["filters"]
except Exception as e:
    print(f"❌ Config error: {e}")
    sys.exit(1)

# === DB ===
try:
    pg_conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    pg_cursor = pg_conn.cursor()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

def already_downloaded(work_id: str) -> bool:
    try:
        pg_cursor.execute("SELECT 1 FROM openalex_works WHERE id = %s", (work_id,))
        return pg_cursor.fetchone() is not None
    except Exception as e:
        print(f"⚠️ Database query failed: {e}")
        return False

# === Filter helpers (RESTORED NORMALIZATION) ===
def _to_oa_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)

def _normalize_kv(key, val):
    # language: allow "en" → "languages/en"
    if key == "language" and isinstance(val, str) and not val.startswith("languages/"):
        return key, f"languages/{val}"
    return key, val

def build_url(cursor="*", page=None):
    parts = []
    # pass-through keys with normalization and OR for lists
    for key, val in FILTERS.items():
        if key in ("from_date", "to_date"):
            continue  # mapped below
        key, val = _normalize_kv(key, val)
        if isinstance(val, list):
            joined = "|".join(_to_oa_value(x) for x in val)
            parts.append(f"{key}:{joined}")
        else:
            parts.append(f"{key}:{_to_oa_value(val)}")
    # map convenience date keys
    if "from_date" in FILTERS:
        parts.append(f"from_publication_date:{FILTERS['from_date']}")
    if "to_date" in FILTERS:
        parts.append(f"to_publication_date:{FILTERS['to_date']}")
    params = {
        "filter": ",".join(parts),
        "per_page": config.get("per_page", PER_PAGE),
        "mailto": EMAIL,
    }
    if sort := config.get("sort"):
        params["sort"] = sort
    if config.get("use_cursor", True):
        params["cursor"] = cursor
    else:
        params["page"] = config.get("page", page or 1)
    return f"{BASE_URL}?{urlencode(params)}"

def get_pdf_url(work):
    locations = []
    if work.get("best_oa_location"):
        locations.append(work["best_oa_location"])
    locations.extend(work.get("locations", []))
    for loc in locations:
        if not loc:
            continue
        url = loc.get("pdf_url")
        if not url or is_blocked(url):
            continue
        return url
    return None

def download_paper(work):
    work_id = work["id"]
    short_id = work_id.split("/")[-1]
    pdf_url = get_pdf_url(work)
    if not pdf_url:
        print(f"⚠️ Skipping (no/blocked PDF): {short_id}")
        return False
    meta_path = os.path.join(META_DIR, f"{short_id}.json")
    pdf_path = os.path.join(PDF_DIR, f"{short_id}.pdf")
    try:
        with open(meta_path, "w") as f:
            json.dump(work, f, indent=2)
        for attempt in range(RETRY_COUNT + 1):
            try:
                r = requests.get(pdf_url, headers=HEADERS, timeout=30)
                r.raise_for_status()
                with open(pdf_path, "wb") as f:
                    f.write(r.content)
                pt = work.get("primary_topic") or {}
                pt_name = pt.get("display_name", "Unknown")
                print(f"✅ Downloaded {short_id} [{pt_name}]")
                return True
            except Exception as e:
                if attempt < RETRY_COUNT:
                    print(f"❌ Download error {short_id}, retrying: {e}")
                    time.sleep(RETRY_DELAY)
                    continue
                print(f"❌ Failed {short_id}: {e}")
                return False
    except Exception as e:
        print(f"❌ File operation failed {short_id}: {e}")
        return False

def probe():
    url = build_url(cursor="*")
    print(f"🔍 Probe URL: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        print(f"✅ Probe OK. Estimated total: {data.get('meta', {}).get('count', '?')}")
    except Exception as e:
        print(f"❌ Probe request failed: {e}")

def run():
    with open(LOG_PATH, "w") as f:
        f.write("filename,publication_date,download_time,primary_topic_id,primary_topic_name\n")
    total = 0
    cursor = "*"
    try:
        while total < DOWNLOAD_LIMIT:
            url = build_url(cursor=cursor)
            print(f"🔍 Fetching: {url}")
            try:
                r = requests.get(url, headers=HEADERS, timeout=60)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"❌ API request failed: {e}")
                break
            results = data.get("results", [])
            if not results:
                break
            for work in results:
                if total >= DOWNLOAD_LIMIT:
                    break
                if already_downloaded(work["id"]):
                    continue
                if download_paper(work):
                    pt = work.get("primary_topic") or {}
                    pt_id = pt.get("id", "")
                    pt_name = pt.get("display_name", "")
                    with open(LOG_PATH, "a") as f:
                        f.write(f"{work['id'].split('/')[-1]}.pdf,{work.get('publication_date','')},{datetime.now().isoformat()},{pt_id},{pt_name}\n")
                    total += 1
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break
    finally:
        pg_conn.close()
    print(f"\n🎉 Finished. Downloaded {total} papers.")
    print(f"📊 Log saved to: {LOG_PATH}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()
    if args.probe:
        probe()
    else:
        run()
