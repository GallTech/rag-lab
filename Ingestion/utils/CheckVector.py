#!/usr/bin/env python3
import os
import sys
import json
import requests

# === Qdrant Config (env-driven, with sane defaults) ===
QDRANT_SCHEME = os.getenv("QDRANT_SCHEME", "http")
QDRANT_HOST   = os.getenv("QDRANT_HOST",   "192.168.0.11")  # your DB VM
QDRANT_PORT   = os.getenv("QDRANT_PORT",   "6333")
QDRANT_APIKEY = os.getenv("QDRANT_API_KEY")  # optional, usually not set
EXPECT_DIM    = os.getenv("EXPECT_VECTOR_DIM")  # optional: e.g. "768"

BASE = f"{QDRANT_SCHEME}://{QDRANT_HOST}:{QDRANT_PORT}"

def _headers():
    h = {"Accept": "application/json"}
    if QDRANT_APIKEY:
        h["api-key"] = QDRANT_APIKEY
    return h

def _get(path, **kw):
    url = f"{BASE}{path}"
    r = requests.get(url, headers=_headers(), timeout=10, **kw)
    r.raise_for_status()
    return r.json()

def _post(path, payload, **kw):
    url = f"{BASE}{path}"
    r = requests.post(url, headers={**_headers(), "Content-Type":"application/json"},
                      data=json.dumps(payload), timeout=20, **kw)
    r.raise_for_status()
    return r.json()

def _parse_vectors(vectors_node):
    """
    Qdrant config.params.vectors can be either:
      { "size": 768, "distance": "Cosine" }
    or a dict of named vectors:
      { "text": {"size": 768, "distance":"Cosine"}, "image": {"size":512,...} }
    Return: dict{name -> {"size": int, "distance": str}}
    """
    out = {}
    if not isinstance(vectors_node, dict):
        return out
    if "size" in vectors_node and "distance" in vectors_node:
        out["default"] = {"size": vectors_node.get("size"), "distance": vectors_node.get("distance")}
    else:
        for name, cfg in vectors_node.items():
            if isinstance(cfg, dict) and "size" in cfg:
                out[name] = {"size": cfg.get("size"), "distance": cfg.get("distance")}
    return out

def main():
    print(f"🔗 Qdrant @ {BASE}\n")

    # List collections
    try:
        j = _get("/collections")
        # Qdrant returns either {"result":{"collections":[{"name":...}]}} or {"collections":[...]}
        collections = []
        if isinstance(j, dict) and "result" in j and isinstance(j["result"], dict):
            collections = j["result"].get("collections", [])
        elif isinstance(j, dict):
            collections = j.get("collections", [])
        names = [c.get("name") for c in collections if "name" in c]
        if not names:
            print("ℹ️  No collections found.")
            return
        print("📚 Collections:", ", ".join(names))
    except Exception as e:
        print(f"❌ Failed to list collections: {e}")
        sys.exit(1)

    print("\n== Collection details ==")
    for name in names:
        try:
            meta = _get(f"/collections/{name}")
            # Extract vector config
            vectors_node = (
                meta.get("result", {})
                    .get("config", {})
                    .get("params", {})
                    .get("vectors", {})
            )
            vecs = _parse_vectors(vectors_node)

            # Count points (fast approximate by default; set exact=True for exact)
            cnt = _post(f"/collections/{name}/points/count", {"exact": False})
            points = cnt.get("result", {}).get("count", None)

            # Print summary
            if vecs:
                dims = [f"{k}:{v['size']} ({v.get('distance')})" for k, v in vecs.items()]
                dims_str = "; ".join(dims)
            else:
                dims_str = "unknown"

            line = f"• {name}: vectors = {dims_str}"
            if points is not None:
                line += f" | points = {points}"
            print(line)

            # Optional expectation check
            if EXPECT_DIM:
                try:
                    exp = int(EXPECT_DIM)
                    actual_dims = {v["size"] for v in vecs.values() if "size" in v}
                    if actual_dims and (actual_dims != {exp}):
                        print(f"   ⚠️  dimension mismatch: expected {exp}, found {sorted(actual_dims)}")
                except ValueError:
                    pass

        except Exception as e:
            print(f"   ❌ Error for '{name}': {e}")

if __name__ == "__main__":
    main()