# Database (lab-1-db01)

This VM provides the **state layer** for the lab:

- **PostgreSQL** — authoritative metadata store (works, chunks, pipeline status).
- **Qdrant** — vector database for chunk embeddings and semantic search.

No application services run here.

---

## Canonical paths

- PostgreSQL data: `/var/lib/postgresql/16/main`
- Qdrant data: `/var/lib/qdrant` (bind-mounted to `/qdrant/storage` inside the container)
- Module code (this repo): `/opt/rag-lab/Database`
- Python venv (admin tooling): `/opt/venvs/database`
- Logs: `/var/log/postgresql`, `/var/log/qdrant`
- Live configs: `/etc/postgresql/16/main`, `/etc/qdrant` (templates live in this repo)

State stays under `/var/lib/...`. Code/templates/scripts stay under `/opt/rag-lab/Database`.

---

## Networking

- PostgreSQL: TCP 5432 (LAN only)
- Qdrant HTTP API: TCP 6333 (LAN only)
- Access limited to Ingestion, Embed, Retrieval, and Management VMs.

---

## Repository layout (this folder)

- `config/` — templates only (never live configs)
  - `postgresql.conf.template`
  - `pg_hba.conf.template`
  - `qdrant.yaml.template`
- `migrations/` — optional SQL or Alembic migrations for PostgreSQL schema
- `scripts/` — admin utilities (backup, restore, health checks, maintenance)
- `docs/` — runbooks / SOPs / notes
- `tests/` — smoke & consistency checks
- `.gitignore`
- `README.md`


---

## Qdrant (container)

- Image: `qdrant/qdrant:v1.9.1`
- Container name: `qdrant`
- Bind mount: `/var/lib/qdrant:/qdrant/storage`
- Health probe: `curl -s http://localhost:6333/collections`

---

## Python admin environment

Create once and reuse:

```bash
python3 -m venv /opt/venvs/database
source /opt/venvs/database/bin/activate
python -m pip install --upgrade pip
pip install "psycopg[binary]" qdrant-client pgcli
deactivate
