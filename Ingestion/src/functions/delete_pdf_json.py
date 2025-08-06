import os

# === Config: Staging Paths ===
PDF_DIR = "/home/mike/staging/pdfs"
JSON_DIR = "/home/mike/staging/metadata"

def delete_pair(short_id):
    """
    Deletes both the PDF and JSON file for a given short OpenAlex ID.
    """
    pdf_path = os.path.join(PDF_DIR, f"{short_id}.pdf")
    json_path = os.path.join(JSON_DIR, f"{short_id}.json")

    deleted = {"pdf": False, "json": False}

    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        deleted["pdf"] = True

    if os.path.exists(json_path):
        os.remove(json_path)
        deleted["json"] = True

    return deleted