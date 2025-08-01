import os
import json
import duckdb

# === Paths ===
METADATA_DIR = os.path.expanduser("~/staging/metadata")
DB_PATH = "/mnt/duckdb/rag.duckdb"
TABLE_NAME = "openalex_works"

# === Connect to DuckDB ===
con = duckdb.connect(DB_PATH)

# === Drop existing table if it exists ===
con.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")

# === Create table with deduplication (PRIMARY KEY on id) ===
con.execute(f"""
CREATE TABLE {TABLE_NAME} (
    id TEXT PRIMARY KEY,
    title TEXT,
    doi TEXT,
    publication_year INTEGER,
    publication_date DATE,
    concepts TEXT,
    topics TEXT,
    authorships TEXT,
    primary_topic TEXT,
    full_raw TEXT
)
""")

# === Insert JSON metadata files ===
inserted = 0
skipped = 0

for file in os.listdir(METADATA_DIR):
    if not file.endswith(".json"):
        continue

    filepath = os.path.join(METADATA_DIR, file)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        con.execute(f"""
            INSERT INTO {TABLE_NAME} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("id"),
            data.get("title"),
            data.get("doi"),
            data.get("publication_year"),
            data.get("publication_date"),
            json.dumps(data.get("concepts")),
            json.dumps(data.get("topics")),
            json.dumps(data.get("authorships")),
            json.dumps(data.get("primary_topic")),
            json.dumps(data)
        ))
        inserted += 1
    except duckdb.ConstraintException:
        skipped += 1

# === Done ===
con.close()
print(f"✅ Metadata ingestion complete. Inserted: {inserted}, Skipped (duplicates): {skipped}")