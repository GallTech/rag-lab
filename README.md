# RAG Lab  

This repository contains all scripts and configuration for a Retrieval-Augmented Generation (RAG) lab.  
Each top-level folder represents a **functional stage** in the pipeline.  

The RAG pipeline ingests ~100,000 AI/ML/Math/Stats research papers from SharePoint, including metadata and ACLs, generates embeddings, and serves queries via FastAPI and Streamlit.  

It includes a **SeaweedFS distributed object store** for PDFs, embeddings, and other large binary artifacts.  

## Structure  

- **ManagementScripts/** → VM provisioning, orchestration, backups  
- **Database/** → Schema definitions, migration, and backup scripts  
- **EmbedGeneration/** → Batch embedding generation and model utilities  
- **Ingestion/** → Data acquisition, chunking, and metadata extraction  
- **UI/** → Lightweight Streamlit UI (later upgraded to React)  
- **API/** → FastAPI microservice for query handling  
- **MLExperiments/** → PyTorch experiments for fine-tuning and testing  
- **SharePointSync/** → Document, metadata, and ACL export/sync from SharePoint  
- **Storage/SeaweedFS/** → Object storage for original documents, chunked JSONs, and embedding backups
