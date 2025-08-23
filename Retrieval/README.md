# Retrieval (lab-1-retrieval01)

This VM serves the Retrieval API. It accepts queries, fetches relevant passages from Qdrant/PostgreSQL, and returns results for the UI or other clients.

## Canonical paths
- Runtime code: /opt/rag-lab/Retrieval
- Development clone (scratch work): ~/rag-lab/Retrieval
- Python venv: /opt/venvs/retrieval
- Config (real values): /etc/retrieval/.env
- Logs: /var/log/retrieval/stdout.log and /var/log/retrieval/stderr.log
- Systemd unit: retrieval.service

Only /opt, /etc, and /var are used at runtime. The repo under ~/rag-lab is safe to delete/reclone.

## Networking
- Retrieval HTTP API: TCP 8001 (LAN only)
- Intended clients: UI and Ingestion (as needed)

## Configuration
Real runtime config lives in /etc/retrieval/.env. Example keys:
- HOST=0.0.0.0
- PORT=8001
- QDRANT_URL=http://lab-1-db01:6333
- PG_DSN=postgresql://user:pass@lab-1-db01:5432/dbname
- EMBED_ENDPOINT=http://lab-1-embed01:8000/embed

Keep a template at Retrieval/config/.env.example. Never commit the real /etc/retrieval/.env.

## Repository layout (this folder)
- config/ — templates (example .env)
- deploy/ — helpers to sync code to /opt and restart the service
- docs/ — runbooks and notes (optional)
- setup/ — one-time bootstrap scripts (optional)
- src/ — rag_api.py and related modules
- tests/ — smoke tests
- .gitignore
- README.md

## Service management
- Status: systemctl status retrieval
- Start/Stop/Restart: sudo systemctl [start|stop|restart] retrieval
- Logs (journal): journalctl -u retrieval -f
- Logs (files): tail -f /var/log/retrieval/stderr.log

## Health
- /health — basic readiness probe
- Quick check: curl -s http://localhost:8001/health

## Update process
1) In ~/rag-lab, pull latest:
   - cd ~/rag-lab
   - git checkout dev
   - git pull origin dev
2) Sync to runtime:
   - rsync -a --delete ~/rag-lab/Retrieval/ /opt/rag-lab/Retrieval/
3) Restart and verify:
   - sudo systemctl restart retrieval
   - curl -s http://localhost:8001/health

## Dependency management
- Virtual environment: /opt/venvs/retrieval
- To update dependencies:
  - source /opt/venvs/retrieval/bin/activate
  - pip install -r /opt/rag-lab/Retrieval/requirements.txt
  - deactivate
Do not commit the venv. Keep requirements.txt in the repo.

## Guardrails
- Do not run manually; always use systemd.
- Do not serve from ~/rag-lab; that clone is for Git work only.
- Keep secrets and runtime config in /etc/retrieval/.env, never in Git.
