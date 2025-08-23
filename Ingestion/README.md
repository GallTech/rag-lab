# Ingestion (lab-1-ingestion01)

This module handles **data ingestion** for the RAG lab. It fetches research papers and metadata, validates and normalizes them, and writes artifacts to the shared state layer (PostgreSQL + MinIO). It also kicks off downstream chunking and embedding.

---

## Scope

- **Sources**: OpenAlex, SharePoint (more later).
- **Tasks**:
  - Download metadata and PDFs.
  - Validate structure and file integrity.
  - Write JSON metadata to **PostgreSQL**.
  - Store PDFs in **MinIO** object storage.
  - Coordinate chunking → embedding → verification.

---

## Canonical paths

- Module code: `/opt/rag-lab/Ingestion`
- Virtual env: `/opt/venvs/ingestion`
- Logs: `/var/log/ingestion`
- Temp: `/tmp/ingestion`

State lives under `/var/*` (databases, durable data). Code, templates, and scripts live in `/opt/rag-lab/Ingestion`.

---

## Repository layout

- `controllers/` — pipeline stages (download, validate, upload, chunk, embed, reports)
- `config/` — config templates (API keys, batch sizes, filters)
- `adapters/` — file/schema helpers (validate JSON/PDF, consistency checks)
- `utils/` — one-off maintenance & diagnostics (counts, orphans, cleanup)
- `tests/` — smoke and consistency checks
- `docs/` — runbooks / SOPs
- `.gitignore`
- `README.md`

---

## Quick start (operator-driven)

1. **Activate env**
    - `source /opt/venvs/ingestion/bin/activate`

2. **Sanity report**
    - `python controllers/04_summary_counts.py`

3. **Typical stages**
    - Download: `python controllers/01_download_metadata_and_pdfs.py`
    - Validate: `python controllers/02_validate_downloaded_files.py`
    - Upload:   `python controllers/03_upload_pdfs_and_json.py`
    - Chunk:    `python controllers/09_chunk_pdfs_and_insert_chunks.py`
    - Embed:    `python controllers/10_CreateEmbeddings.py`

4. **Deactivate env**
    - `deactivate`

---

## External dependencies

- **PostgreSQL** (Database VM) — TCP 5432
- **Qdrant** (Database VM) — HTTP 6333
- **MinIO** (Storage VM) — HTTP 9000 (API), 9001 (console)

Access is LAN-only; credentials are provided via environment or local `.env` **not** committed to Git.

---

## Configuration

- Copy templates from `config/` and provide real values via:
  - `/etc/ingestion/.env` (preferred), or
  - exported environment variables in the shell.
- Do **not** commit secrets. `.gitignore` excludes common secret patterns.

---

## Operational tips

- Run reports frequently:
  - `python controllers/04_summary_counts.py` — end-to-end counts & progress
- If a stage fails, re-run the single controller rather than the whole pipeline.
- Use `utils/` scripts for diagnostics (e.g., orphan checks, disk usage, retry helpers).

