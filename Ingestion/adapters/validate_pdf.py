import os
import glob

PDF_DIR = "/home/mike/staging/pdfs"

def validate_all_pdfs():
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    total = len(pdf_files)
    valid = 0
    invalid = 0
    invalid_files = []

    for path in pdf_files:
        size = os.path.getsize(path)
        if size == 0:
            invalid += 1
            invalid_files.append({
                "filename": os.path.basename(path),
                "error": "File is 0 bytes"
            })
        else:
            valid += 1

    return {
        "valid_count": valid,
        "invalid_count": invalid,
        "invalid_files": invalid_files,
        "total_files": total
    }