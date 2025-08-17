#!/bin/bash

# ──────────────────────────────────────────────────────────────
# CONFIGURATION — adapt as needed
# ──────────────────────────────────────────────────────────────

PG_HOST="192.168.0.11"
PG_PORT="5432"
PG_DB="raglab"
PG_USER="mike"

MINIO_ALIAS="local"
MINIO_BUCKET="papers"

QDRANT_HOST="192.168.0.11"
QDRANT_PORT="6333"

EMBEDDING_HOST="192.168.0.12"
EMBEDDING_PORT="8000"
EMBEDDING_ENDPOINT="/health"   # or "/" or "/docs", depending on server

# ──────────────────────────────────────────────────────────────
# CHECK POSTGRESQL
# ──────────────────────────────────────────────────────────────
echo "🔌 Checking PostgreSQL connection..."
PGPASSWORD="$PG_PASSWORD" psql -h "$PG_HOST" -U "$PG_USER" -p "$PG_PORT" -d "$PG_DB" -c '\q'
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL connection OK"
else
    echo "❌ PostgreSQL connection failed"
fi

# ──────────────────────────────────────────────────────────────
# CHECK MINIO
# ──────────────────────────────────────────────────────────────
echo "🗄️  Checking MinIO connection..."
mc alias list | grep -q "$MINIO_ALIAS"
if [ $? -ne 0 ]; then
    echo "❌ MinIO alias '$MINIO_ALIAS' not found. Run 'mc alias set ...'"
else
    mc ls "$MINIO_ALIAS/$MINIO_BUCKET" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ MinIO connection OK (bucket '$MINIO_BUCKET' exists)"
    else
        echo "❌ MinIO connection failed or bucket '$MINIO_BUCKET' not found"
    fi
fi

# ──────────────────────────────────────────────────────────────
# CHECK QDRANT
# ──────────────────────────────────────────────────────────────
echo "📦 Checking Qdrant..."
curl -sSf "http://$QDRANT_HOST:$QDRANT_PORT/healthz" | grep -q "passed"
if [ $? -eq 0 ]; then
    echo "✅ Qdrant health check OK"
else
    echo "❌ Qdrant not responding"
fi

# ──────────────────────────────────────────────────────────────
# CHECK EMBEDDING LLM
# ──────────────────────────────────────────────────────────────
echo "🧠 Checking embedding LLM service..."
EMBEDDING_URL="http://192.168.0.12:8000"
RESPONSE=$(curl --silent -w "%{http_code}" -o /tmp/embed_out \
  -X POST "$EMBEDDING_URL/embed" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["ping"]}')

if [ "$RESPONSE" = "200" ]; then
  echo "✅ Embedding LLM service is responsive at $EMBEDDING_URL/embed"
else
  echo "❌ Embedding LLM returned status code $RESPONSE"
  echo "--- Response body ---"
  cat /tmp/embed_out
  echo "---------------------"
fi

echo "✅ All checks complete."