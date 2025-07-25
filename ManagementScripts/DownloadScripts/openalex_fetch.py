import os
import json
import requests
from urllib.parse import urlencode

# ==== CONFIG ====
OUTPUT_DIR = "downloads"
META_DIR = os.path.join(OUTPUT_DIR, "metadata")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")

os.makedirs(META_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

BASE_URL = "https://api.openalex.org/works"
CONCEPT_MATH = "https://openalex.org/C33923547"  # Mathematics
DATE_FROM = "2025-01-01"
DATE_TO = "2025-12-31"
PER_PAGE = 50

# Only these domains are trusted to actually give PDFs without 403
TRUSTED_OA_DOMAINS = [
    "arxiv.org",
    "osf.io",
    "biorxiv.org",
    "medrxiv.org",
    "europepmc.org",
    "nih.gov/pmc"
]

# ==== HELPERS ====

def build_url(cursor="*"):
    params = {
        "filter": f"concepts.id:{CONCEPT_MATH},from_publication_date:{DATE_FROM},to_publication_date:{DATE_TO},open_access.is_oa:true",
        "per-page": PER_PAGE,
        "cursor": cursor
    }
    return f"{BASE_URL}?{urlencode(params)}"

def get_trusted_pdf_url(work):
    """Pick a PDF URL only from trusted OA domains."""
    candidates = []

    # best OA location
    best = work.get("best_oa_location")
    if best and best.get("pdf_url"):
        candidates.append(best["pdf_url"])

    # all locations
    for loc in work.get("locations", []):
        if loc.get("pdf_url"):
            candidates.append(loc["pdf_url"])

    # return first trusted match
    for url in candidates:
        if any(domain in url for domain in TRUSTED_OA_DOMAINS):
            return url
    return None

def download_pdf_and_metadata(work, pdf_url):
    """Save metadata JSON + PDF to disk."""
    title_safe = "".join(c for c in work["title"] if c.isalnum() or c in (" ", "_", "-"))[:100]
    work_id = work["id"].split("/")[-1]

    meta_path = os.path.join(META_DIR, f"{work_id}.json")
    pdf_path = os.path.join(PDF_DIR, f"{work_id}.pdf")

    # skip duplicates
    if os.path.exists(pdf_path):
        print(f"✅ Already downloaded: {title_safe}")
        return

    # save metadata
    with open(meta_path, "w") as f:
        json.dump(work, f, indent=2)

    # download PDF
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
    print("=== Starting OpenAlex download for 2025 Mathematics ===")
    cursor = "*"
    total_downloads = 0
    download_limit = 1000  # change if you want fewer/more

    while total_downloads < download_limit:
        url = build_url(cursor)
        print(f"\nFetching page (cursor={cursor}) ...")
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()

        # iterate works
        for work in data["results"]:
            if total_downloads >= download_limit:
                break

            pdf_url = get_trusted_pdf_url(work)
            if not pdf_url:
                # skip if no trusted PDF
                continue

            download_pdf_and_metadata(work, pdf_url)
            total_downloads += 1

        # break if no next page
        meta = data.get("meta", {})
        cursor = meta.get("next_cursor")
        if not cursor:
            print("No more pages.")
            break

    print(f"=== Done. Total downloaded: {total_downloads} ===")

if __name__ == "__main__":
    main()