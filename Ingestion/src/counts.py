import requests

def get_openalex_count():
    url = (
        "https://api.openalex.org/works?"
        "filter=title_and_abstract.search:AI,"
        "open_access.is_oa:true,"
        "publication_year:2023-2025"
        "&per_page=1"
        "&mailto=mike.gallagher@live.ie"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("meta", {}).get("count", 0)

if __name__ == "__main__":
    count = get_openalex_count()
    print(f"Total matching works: {count}")