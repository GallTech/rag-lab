export QDRANT_URL="http://192.168.0.11:6333"
curl -sS -X PUT "$QDRANT_URL/collections/openalex" \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": { "size": 768, "distance": "Cosine" },
    "hnsw_config": { "m": 16, "ef_construct": 256 },
    "optimizers_config": { "default_segment_number": 2 }
  }' | jq .

  curl -sS -X PUT "$QDRANT_URL/collections/openalex/index" \
  -H 'Content-Type: application/json' \
  -d '{"field_name":"work_id","field_schema":"keyword"}' | jq .

  export QDRANT_URL="http://192.168.0.11:6333"

# Inspect collection config
curl -s "$QDRANT_URL/collections/openalex" | jq '.result.config.params.vectors'