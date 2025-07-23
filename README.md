# RAG Lab  

This repository contains all scripts and configs for the entire RAG Lab setup.
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
