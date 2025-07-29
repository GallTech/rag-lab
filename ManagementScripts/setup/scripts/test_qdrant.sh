# Create a test collection with 4D vectors
curl -X PUT "http://localhost:6333/collections/test_collection" \
  -H 'Content-Type: application/json' \
  -d '{
        "vectors": {
          "size": 4,
          "distance": "Cosine"
        }
      }'

# Insert two dummy vectors
curl -X PUT "http://localhost:6333/collections/test_collection/points?wait=true" \
  -H 'Content-Type: application/json' \
  -d '{
        "points": [
          {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"doc": "first"}},
          {"id": 2, "vector": [0.9, 0.8, 0.7, 0.6], "payload": {"doc": "second"}}
        ]
      }'

# Query for the nearest vector
curl -X POST "http://localhost:6333/collections/test_collection/points/search" \
  -H 'Content-Type: application/json' \
  -d '{
        "vector": [0.05, 0.1, 0.2, 0.3],
        "limit": 1
      }'