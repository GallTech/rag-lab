import os
import json
import requests
from urllib.parse import urlencode
import time

# Config
EMAIL = "mike.gallagher@live.ie"
OUTPUT_DIR = os.path.expanduser("~/staging")
META_DIR = os.path.join(OUTPUT_DIR, "metadata")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")
PER_PAGE = 50
DOWNLOAD_LIMIT = 1000
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds
BASE_URL = "https://api.openalex.org/works"
TRUSTED_OA_DOMAINS = [
    "arxiv.org", "osf.io", "biorxiv.org", "medrxiv.org", "europepmc.org", "nih.gov/pmc"
]

os.makedirs(META_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

def build_url(cursor="*"):
    params = {
        "filter": "title_and_abstract.search:AI,open_access.is_oa:true,publication_year:2023-2025",
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
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            with open(path, "wb") as f:
                f.write(resp.content)
            return True
        except Exception as e:
            print(f"Attempt {attempt} failed for {url}: {e}")
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
    return False

def download_pdf_and_metadata(work, pdf_url):
    work_id = work["id"].split("/")[-1]
    meta_path = os.path.join(META_DIR, f"{work_id}.json")
    pdf_path = os.path.join(PDF_DIR, f"{work_id}.pdf")

    # Save metadata
    with open(meta_path, "w") as f:
        json.dump(work, f, indent=2)

    # Download PDF with retries
    success = download_with_retries(pdf_url, pdf_path)
    if success:
        print(f"✅ Downloaded: {work['title'][:80]}...")
    else:
        print(f"❌ Failed to download PDF for: {work['title'][:80]}")

def main():
    cursor = "*"
    total_downloaded = 0

    while total_downloaded < DOWNLOAD_LIMIT:
        url = build_url(cursor)
        print(f"Fetching page (cursor={cursor})...")
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()

        for work in data["results"]:
            if total_downloaded >= DOWNLOAD_LIMIT:
                break
            pdf_url = get_trusted_pdf_url(work)
            if pdf_url:
                download_pdf_and_metadata(work, pdf_url)
                total_downloaded += 1

        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            print("No more pages.")
            break

    print(f"Finished downloading {total_downloaded} papers.")

if __name__ == "__main__":
    main()