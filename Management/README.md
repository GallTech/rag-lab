# Management

This folder is currently a placeholder and does not contain any working code. 

This folder contains infrastructure-as-code and automation for the **Management VM**.  
The Management VM is responsible for orchestrating and maintaining the overall RAG lab environment.

## Contents
- **ansible/** — Playbooks, roles, and inventories for configuring services.
- **terraform/** — Terraform configs for provisioning resources (on-prem/Proxmox or cloud).
- **kubernetes/** — Base manifests, Helm values, and Kustomize overlays.
- **proxmox/** — Proxmox automation, cloud-init templates, and VM lifecycle scripts.
- **backup/** — Backup scripts, retention policies, and restore procedures.
- **scripts/** — One-off helpers for infra tasks.
- **docs/** — Documentation and architecture notes.
- **tests/** — Infrastructure validation (e.g. Molecule for Ansible roles).