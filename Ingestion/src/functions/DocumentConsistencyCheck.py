import os

# === Config ===
JSON_DIR = "/home/mike/staging/metadata"
PDF_DIR = "/home/mike/staging/pdfs"

def check_and_delete_orphans():
    json_ids = {
        f.replace(".json", "")
        for f in os.listdir(JSON_DIR)
        if f.endswith(".json")
    }

    pdf_ids = {
        f.replace(".pdf", "")
        for f in os.listdir(PDF_DIR)
        if f.endswith(".pdf")
    }

    deleted = []

    # JSONs with no PDF
    for id_ in json_ids - pdf_ids:
        json_path = os.path.join(JSON_DIR, f"{id_}.json")
        if os.path.exists(json_path):
            os.remove(json_path)
            deleted.append(f"{id_}.json")

    # PDFs with no JSON
    for id_ in pdf_ids - json_ids:
        pdf_path = os.path.join(PDF_DIR, f"{id_}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            deleted.append(f"{id_}.pdf")

    return {"deleted": deleted}