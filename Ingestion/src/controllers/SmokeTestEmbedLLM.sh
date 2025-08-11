EMBED_URL="http://192.168.0.12:8000"
QDRANT_URL="http://192.168.0.11:6333"
COLL="openalex"

# 1) Embed
VEC=$(curl -sS -X POST "$EMBED_URL/embed" \
  -H 'Content-Type: application/json' \
  -d '{"texts":["hello qdrant"]}' | jq -c '.embeddings[0]')
echo "dim: $(echo "$VEC" | jq 'length')"

# 2) Health: collection info
curl -sS "$QDRANT_URL/collections/$COLL" | jq .

# 3) Upsert one point
curl -sS -X PUT "$QDRANT_URL/collections/$COLL/points" \
  -H 'Content-Type: application/json' \
  -d "{\"points\":[{\"id\":1,\"vector\":$VEC,\"payload\":{\"work_id\":\"test-1\",\"note\":\"smoke\"}}]}" | jq .

# 4) Search it back
curl -sS -X POST "$QDRANT_URL/collections/$COLL/points/search" \
  -H 'Content-Type: application/json' \
  -d "{\"vector\":$VEC,\"limit\":3}" | jq .