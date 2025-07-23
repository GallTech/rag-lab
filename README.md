# RAG Lab  

This repository contains scripts and config for a RAG Lab setup consuming SharePoint data.
Each folder corresponds to a **functional stage** in the pipeline.

## Structure

- **ManagementScripts/** → VM management, backups, orchestration
- **Database/** → Database schema, migration, backup scripts
- **EmbedGeneration/** → Scripts to generate embeddings in batch
- **Ingestion/** → Data collection, chunking, metadata extraction
- **UI/** → Streamlit UI (later React)
- **API/** → FastAPI microservice
- **MLExperiments/** → PyTorch experiments for fine-tuning

Each VM clones this repo but only uses its relevant folder.

**Status:** Early provisioning & scaffolding.  
