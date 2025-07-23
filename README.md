# RAG Lab  

This repository contains all scripts and configuration for a Retrieval-Augmented Generation (RAG) lab.  
Each top-level folder represents a functional stage in the pipeline.  

The RAG pipeline ingests ~100,000 AI/ML/Math/Stats research papers from SharePoint, including metadata and ACLs, generates embeddings, and serves queries via FastAPI and Streamlit.  

## Structure  

- **ManagementScripts/** → VM provisioning, orchestration, and backups using **Terraform** and **Ansible**  
- **Database/** →  
  - **Qdrant** for vector storage & similarity search  
  - **DuckDB** for metadata (titles, authors, categories, ACLs) and lightweight relational queries  
  - Includes schema definitions, migration scripts, and backup utilities  
- **EmbedGeneration/** → Batch embedding generation and model utilities (e.g. `sentence-transformers/all-MiniLM-L6-v2`, `BAAI/bge-large-en`, and local LLaMA/embedding models)  
- **Ingestion/** → Data acquisition, text chunking, and metadata extraction from PDFs and SharePoint documents  
- **UI/** → Lightweight **Streamlit UI** & **React prototype** for query exploration and visualization  
- **API/** → **FastAPI** microservice for query handling and document retrieval  
- **MLExperiments/** → **PyTorch** fine-tuning and testing workflows for domain-specific models  
- **SharePointSync/** → **PowerShell**, **Microsoft Graph API**, and **PnP** scripts for document, metadata, and ACL export/sync from SharePoint  
- **Storage/** → Object storage in **SeaweedFS** for original documents, chunked JSONs, and embedding backups  

## Current Status  
Early provisioning & scaffolding.  

## Infrastructure  
Proxmox hosted on **Minisforum UM890 Pro (Ryzen 9 8945HS, 64 GB DDR5, 2 TB NVMe)**  
