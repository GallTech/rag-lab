import os
import duckdb
import json

# Paths
METADATA_DIR = os.path.expanduser("~/staging/metadata")
DB_PATH = "/mnt/duckdb/rag.duckdb"
TABLE_NAME = "openalex_works"

# Connect to DuckDB
con = duckdb.connect(DB_PATH)

# Create table with safe TEXT columns instead of JSON (you can query JSON using DuckDB functions)
con.execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id TEXT,
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

# Load and insert each JSON file
for file in os.listdir(METADATA_DIR):
    if not file.endswith(".json"):
        continue

    filepath = os.path.join(METADATA_DIR, file)
    with open(filepath) as f:
        data = json.load(f)

    # Use .get() to safely extract fields
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

con.close()
print("✅ All metadata inserted successfully into DuckDB.")