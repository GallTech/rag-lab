#!/usr/bin/env python3
import requests

QDRANT_URL = "http://192.168.0.11:6333"
COLL = "openalex"

def get_vector_size():
    # If you already know the embed size, hardcode it (e.g., 768) and skip this probe.
    probe = [0.0] * 768  # <-- change if your embed size differs
    return len(probe)

base = f"{QDRANT_URL}/collections/{COLL}"

# 1) Delete collection if exists
r = requests.get(base, timeout=10)
if r.status_code == 200:
    print(f"🗑️  Deleting existing collection '{COLL}'...")
    rd = requests.delete(base, timeout=30)
    rd.raise_for_status()
    print("✅ Deleted.")
elif r.status_code != 404:
    r.raise_for_status()

# 2) Recreate collection
vec_size = get_vector_size()
print(f"🆕 Creating '{COLL}' with size={vec_size}, distance=Cosine...")
rc = requests.put(base, json={"vectors": {"size": vec_size, "distance": "Cosine"}}, timeout=30)
rc.raise_for_status()
print("✅ Created fresh collection.")
