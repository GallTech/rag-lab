# RAG Lab  

This repository contains all scripts and configuration for a Retrieval-Augmented Generation (RAG) lab.  
Each top-level folder represents a functional stage in the pipeline.  

The RAG pipeline ingests ~100,000 AI/ML/Math/Stats research papers from SharePoint and other sources, extracts metadata and ACLs, and generates vector embeddings.  

- It can use **OpenAI’s ChatGPT**, **Google Gemini**, or **local models** (e.g. **LLaMA/Mistral**) as the LLM backend.  
- All components—ingestion, embedding, vector storage, and LLM reasoning—are **interchangeable**, so you can swap providers without changing the pipeline.  
- By design, **retrieval is decoupled from generation**, making it easy to upgrade or mix different LLMs for different tasks.  

## Process  

1. **Extracts documents from SharePoint** with metadata + ACLs  
2. **Chunks and embeds content** using configurable embedding models  
3. **Stores vector representations in Qdrant** for fast similarity search  
4. **Retrieves context via LangChain + prompt engineering**  
5. **Generates answers with a pluggable LLM backend** – OpenAI ChatGPT, Google Gemini, or local models – served via FastAPI & Streamlit  

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
