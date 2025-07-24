# RAG Lab  

This repository contains configuration and code for a Retrieval-Augmented Generation (RAG) lab.  

Each top-level folder represents a functional stage in the pipeline.  

The RAG pipeline ingests ~100,000 AI/ML/Math/Stats research papers from **SharePoint**, **OpenAlex**, and other sources, extracts metadata and ACLs, and generates vector embeddings.  

- It can use **OpenAI’s ChatGPT**, **Google Gemini**, or **local models** (e.g. **LLaMA/Mistral**) as the LLM backend.  
- All components—ingestion, embedding, vector storage, and LLM reasoning—are **interchangeable**, so you can swap providers without changing the pipeline.  
- By design, **retrieval is decoupled from generation**, making it easy to upgrade or mix different LLMs for different tasks.  

## Process

1. **Collects documents** from SharePoint and OpenAlex with metadata and ACLs *(see Data Ingestion section for details)*  
2. **Stores originals in SeaweedFS** with references in DuckDB  
3. **Chunks and embeds content** using configurable embedding models  
4. **Stores vector representations in Qdrant** for fast similarity search  
5. **Retrieves relevant context** with LangChain + custom Python retrievers  
6. **Generates answers via a pluggable LLM backend** (OpenAI, Gemini, or local models)  
7. **Serves responses** through FastAPI & Streamlit  

## Monitoring  

A dedicated **monitoring server** (`lab-1-monitoring`) runs:  
- **Prometheus** for metrics collection  
- **Grafana** for dashboards  
- **Alertmanager** for notifications  
- Nightly integrity checks to ensure DuckDB → SeaweedFS references remain valid  

## Project Structure  

- **ManagementScripts/** → VM provisioning, orchestration, and backups with Terraform + Ansible  
- **Database/** → Qdrant for vectors, DuckDB for metadata  
- **EmbedGeneration/** → Embedding generation utilities  
- **Ingestion/** → SharePoint + OpenAlex pipelines  
- **Storage/** → SeaweedFS for original documents  
- **Monitoring/** → Prometheus, Grafana, integrity checker  
- **UI/** → Streamlit & React prototypes for queries  
- **API/** → FastAPI microservice for retrieval + LLM  
- **MLExperiments/** → Fine-tuning & testing workflows  

## Infrastructure  
Proxmox hosted on Minisforum UM890 Pro (Ryzen 9 8945HS, 64 GB DDR5, 2 TB NVMe)  

## Current Status  
Early build
