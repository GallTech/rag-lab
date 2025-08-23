# Storage (lab-1-storage01)

Object storage for the RAG lab (MinIO). Holds PDFs, JSON artifacts, logs, and any binary outputs. No app logic runs here.

## Canonical paths
- Data volume: /mnt/storage (via MINIO_VOLUMES)
- Config (real): /etc/default/minio
- Service: minio.service
- Logs: journalctl -u minio (and /var/log/syslog if needed)
- Console: http://<storage-ip>:9001
- S3 API: http://<storage-ip>:9000

## Repo layout (this folder)
- config/ — templates (e.g., minio.conf.example). Never commit real credentials.
- scripts/ — helpers to create buckets, policies, lifecycles (uses mc).
- docs/ — runbooks (backup/restore, rotate creds, lifecycle rules).
- tests/ — smoke checks (e.g., mc alias ping, bucket exists).
- .gitignore — excludes data/state and secrets.

## Quick ops
- Check status: systemctl status minio
- Tail logs: journalctl -u minio -f
- Disk: df -h; sudo du -sh /mnt/storage
- Ports: 9000 (API), 9001 (Console)

## mc setup (example)
mc alias set minio http://<storage-ip>:9000 <ROOT_USER> <ROOT_PASSWORD>
mc ls minio
