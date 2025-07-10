# RAG Lab Environment

This repository contains the full infrastructure and modular application code for a Retrieval-Augmented Generation (RAG) lab using SharePoint data.

The environment runs on a Proxmox virtualized platform with clear separation of concerns: each virtual machine hosts a specific role, such as vector storage, ingestion, or embedding services. Embedding is provided as a dedicated service for performance and modularity. Terraform, Ansible, and cloud-init manage all provisioning (`/infrastructure`).

FastAPI is deployed to Kubernetes (`/kubernetes`) for scalable, containerized query serving, with long-term plans to migrate additional workloads as performance and observability permit. All other components currently run directly on VMs for maximum speed and hardware control.

### Structure

- `infrastructure/` – Terraform, Ansible, and cloud-init
- `kubernetes/` – K8s manifests (FastAPI, monitoring)
- `rag_functions/` – Modular RAG pipeline logic
- `shared/` – Reusable code (e.g., logging, config)
- `docs/` – Deployment and architecture notes

