# Model (lab-1-model01)

This module is for model training, fine-tuning, reranking, and related experimental code. Currently a placeholder. 

## Scope
- Offline experiments: data prep, fine-tuning, evaluation, reranking.
- No production endpoints live here.

## Canonical (planned) paths
- Runtime code (future): /opt/rag-lab/Model
- Venv (future): /opt/venvs/model
- Config (real values, future): /etc/model/.env
- Logs (future): /var/log/model
- Datasets (never in Git): /data/training (or mounted volume)
- Model artifacts (never in Git): /var/lib/model/artifacts or /data/models

Only templates and code live in this repo; large files and secrets stay under /data, /var, or /etc.

## Repository layout
- config/ — templates, example configs (no real secrets)
- docs/ — experiment notes, runbooks
- notebooks/ — exploratory work (small samples only)
- scripts/ — CLI tools for data prep, training, eval
- src/ — reusable training/eval code (importable)
- tests/ — smoke tests (e.g., import checks, tiny dataset runs)
- .gitignore — excludes datasets, models, logs, venvs
- README.md — this file
