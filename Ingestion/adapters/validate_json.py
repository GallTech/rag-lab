# /home/mike/rag-lab/Ingestion/src/DocProcessFunctions/ValidateJson.py

import os
import json
import glob
from jsonschema import validate, ValidationError

def load_schema(path):
    with open(path, 'r') as f:
        return json.load(f)

def validate_metadata_files(metadata_dir, schema):
    json_files = glob.glob(os.path.join(metadata_dir, "*.json"))
    total = len(json_files)
    valid = 0
    invalid = 0
    invalid_files = []

    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                validate(instance=data, schema=schema)
                valid += 1
        except (json.JSONDecodeError, ValidationError) as e:
            invalid += 1
            invalid_files.append({
                "filename": os.path.basename(file_path),
                "error": str(e).splitlines()[0]
            })

    return {
        "valid_count": valid,
        "invalid_count": invalid,
        "invalid_files": invalid_files,
        "total_files": total
    }

def validate_all_json_files(schema_path, json_dir):
    schema = load_schema(schema_path)
    return validate_metadata_files(json_dir, schema)