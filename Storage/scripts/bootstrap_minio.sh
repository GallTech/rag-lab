#!/usr/bin/env bash
set -euo pipefail
# Requires: mc alias already set (e.g., mc alias set minio http://<host>:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD)
# Create buckets
mc mb -p minio/openalex || true
mc mb -p minio/chunks   || true
mc mb -p minio/logs     || true
# Example: set lifecycle to expire old logs
mc ilm add --expiration-days 30 minio/logs
# Example: read-only policy for retrieval
mc admin policy create minio read-openalex - <<'POL'
{
  "Version":"2012-10-17",
  "Statement":[{"Effect":"Allow","Action":["s3:GetBucketLocation","s3:ListBucket"],"Resource":["arn:aws:s3:::openalex"]},
               {"Effect":"Allow","Action":["s3:GetObject"],"Resource":["arn:aws:s3:::openalex/*"]}]
}
POL
# Attach policy to user (expects user created elsewhere)
# mc admin user add minio retrieval-user <password>
# mc admin policy attach minio read-openalex --user retrieval-user
echo "MinIO bootstrap complete."
