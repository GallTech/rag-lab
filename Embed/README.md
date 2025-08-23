# EmbedGeneration (lab-1-embed01)

This VM hosts the embedding service. It exposes a FastAPI app (served by Uvicorn) that generates embeddings using the model `nomic-embed-text-v1` and makes them available to the rest of the RAG lab.

---

## Canonical paths

- Runtime code: `/opt/rag-lab/EmbedGeneration`
- Development clone (scratch work): `~/rag-lab` (safe to delete/reclone)
- Python venv: `/opt/venvs/embed`
- Config: `/etc/embed/.env`
- Logs: `/var/log/embed/stdout.log`, `/var/log/embed/stderr.log`
- Systemd unit: `/etc/systemd/system/embed.service`

Only `/opt`, `/etc`, and `/var` are used at runtime. `~/rag-lab` is just a Git workspace.

---

## Networking

- Service HTTP API: TCP **8000** (LAN only)
- Expected clients: Ingestion (batch jobs), Retrieval (on-demand)

---

## Configuration

Runtime configuration lives in `/etc/embed/.env`. Example:

```
HOST=0.0.0.0
PORT=8000
QDRANT_URL=http://lab-1-db01:6333
PG_DSN=postgresql://user:pass@lab-1-db01:5432/dbname
EMBED_MODEL=nomic-embed-text-v1
```

---

## Repository layout (this folder)

- `config/` — templates (example `.env`)
- `docs/` — runbooks / notes
- `tests/` — smoke tests for API endpoints
- `.gitignore`
- `README.md`

---

## Service management

Check status:
```
systemctl status embed
```

Start / stop / restart:
```
sudo systemctl start embed
sudo systemctl stop embed
sudo systemctl restart embed
```

Logs (journal):
```
journalctl -u embed -f
```

Logs (files):
```
tail -f /var/log/embed/stdout.log
tail -f /var/log/embed/stderr.log
```

---

## Health and endpoints

- `/docs` — FastAPI auto-docs
- `/health` — simple status endpoint (if implemented)
- `/embed` — POST endpoint for embedding text chunks

Quick local check:
```
curl -s http://localhost:8000/health || curl -s http://localhost:8000/docs | head
```

---

## Update process (deploy new code)

1) Update the dev clone:
```
cd ~/rag-lab
git checkout dev
git pull origin dev
```

2) Sync into the runtime location:
```
rsync -a --delete ~/rag-lab/EmbedGeneration/ /opt/rag-lab/EmbedGeneration/
```

3) Restart and verify:
```
sudo systemctl restart embed
curl -s http://localhost:8000/health
```

---

## Dependency management

Virtual environment: `/opt/venvs/embed`

To update dependencies:
```
source /opt/venvs/embed/bin/activate
pip install -r /opt/rag-lab/EmbedGeneration/requirements.txt
deactivate
```
