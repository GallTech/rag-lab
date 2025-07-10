# RAG Lab Environment

This repository contains the infrastructure and application code for a Retrieval-Augmented Generation (RAG) lab using SharePoint data.

The environment runs on a Proxmox virtualized platform with clear separation of concerns: each virtual machine hosts a specific role, such as vector storage, ingestion, or embedding services. Embedding is performed locally using the `all-MiniLM-L6-v2` model from `sentence-transformers`, running as a dedicated service for performance and modularity. Infrastructure is provisioned and managed via Terraform, Ansible, and cloud-init (`/infrastructure`).

FastAPI is deployed to Kubernetes (`/kubernetes`) for scalable, containerized query serving. The RAG LLM is currently configured to use ChatGPT, but this is fully configurable and can be swapped with a local or remote model as needed.

## Structure

- `infrastructure/` – Terraform, Ansible, and cloud-init
- `kubernetes/` – K8s manifests (FastAPI, monitoring)
- `rag_functions/` – Modular RAG pipeline logic
- `shared/` – Reusable code (e.g., logging, config)
- `docs/` – Deployment and architecture notes
- `react_ui/` – Frontend interface (React)

## Status

🧪 Early stage – initial scaffolding in progress.
