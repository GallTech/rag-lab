import sys
import os

# === Import validation functions and delete helper ===
from adapters.validate_json import validate_all_json_files
from adapters.validate_pdf import validate_all_pdfs
from adapters.delete_pdf_json import delete_pair
from adapters.document_consistency_check import check_and_delete_orphans

# === Constants ===
SCHEMA_PATH = "/home/mike/rag-lab/Ingestion/schemas/openalex_work.schema.json"
JSON_DIR = "/home/mike/staging/metadata"

# === Main ===
def main():
    print("🚀 Starting document processing pipeline...\n")

    # === Step 1: Validate JSON files ===
    print("🔍 Step 1: Validating JSON files...")
    result = validate_all_json_files(schema_path=SCHEMA_PATH, json_dir=JSON_DIR)

    print("\n✅ JSON validation complete.")
    print(f"   - Valid files: {result['valid_count']}")
    print(f"   - Invalid files: {result['invalid_count']}")
    print(f"   - Total files: {result['total_files']}")

    if result["invalid_files"]:
        print("\n🧨 Invalid JSON files summary:")
        for item in result["invalid_files"]:
            print(f" - {item['filename']}: {item['error']}")
            short_id = item["filename"].replace(".json", "")
            deleted = delete_pair(short_id)
            if deleted["pdf"] or deleted["json"]:
                print(f"   🗑️ Deleted files for {short_id}: {deleted}")

    # === Step 2: Validate PDFs ===
    print("\n🔍 Step 2: Validating PDF files...")
    pdf_result = validate_all_pdfs()

    print("\n✅ PDF validation complete.")
    print(f"   - Valid files: {pdf_result['valid_count']}")
    print(f"   - Invalid files: {pdf_result['invalid_count']}")
    print(f"   - Total files: {pdf_result['total_files']}")

    if pdf_result["invalid_files"]:
        print("\n🧨 Invalid PDF files summary:")
        for item in pdf_result["invalid_files"]:
            print(f" - {item['filename']}: {item['error']}")
            short_id = item["filename"].replace(".pdf", "")
            deleted = delete_pair(short_id)
            if deleted["pdf"] or deleted["json"]:
                print(f"   🗑️ Deleted files for {short_id}: {deleted}")

    # === Step 3: Consistency Check ===
    print("\n🔍 Step 3: Checking for orphaned files...")
    orphans = check_and_delete_orphans()
    if orphans["deleted"]:
        print(f"   🗑️ Deleted orphans: {orphans['deleted']}")
    else:
        print("   ✅ No orphans found.")

    print("\n🎯 Done.")

if __name__ == "__main__":
    main()