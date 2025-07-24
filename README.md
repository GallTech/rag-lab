# RAG Lab: Modular Pipeline for Research Paper Retrieval & Generation  

A production-grade RAG system for ingesting, embedding, and querying ~100K AI/ML/Math/Stats papers. Supports OpenAI, Gemini, and local LLMs with fully decoupled components for flexibility.  

Each top-level folder represents a functional stage in the pipeline. The lab ingests ~100,000 AI/ML/Math/Stats research papers from **SharePoint**, **OpenAlex**, and other sources, extracts metadata and ACLs, and generates vector embeddings for retrieval-augmented LLM reasoning.  

- **Flexible LLM backends**: OpenAI’s ChatGPT, Google Gemini, or local models (e.g., LLaMA/Mistral).  
- **Interchangeable components**: ingestion, embedding, vector storage, retrieval orchestration, and LLM reasoning are decoupled.  
- **Retrieval-first design**: retrieval is separated from generation, making it easy to mix or upgrade LLMs for different tasks.  
- **LangChain-based orchestration**: dynamic context assembly & prompt engineering before LLM calls.  

---

## Process  

1. **Collect documents** from SharePoint and OpenAlex with metadata + ACLs *(see Data Ingestion section for details)*  
2. **Store original PDFs in SeaweedFS**, with metadata indexed in DuckDB  
3. **Chunk & embed content** using configurable embedding models  
   - e.g. OpenAI `text-embedding-ada-002` or local Sentence Transformers  
4. **Store vector representations in Qdrant** for fast similarity search  
5. **Retrieve relevant context** using **LangChain retrievers + custom Python logic**  
6. **Assemble context & craft prompts dynamically** for the target LLM backend  
7. **Generate answers via pluggable LLM backend** (OpenAI, Gemini, or local models)  
8. **Serve responses** through FastAPI & Streamlit (**React + TypeScript UI under development**)  

---

## Monitoring  

A dedicated **monitoring server** (`lab-1-monitoring`) runs:  
- **Prometheus** for metrics collection  
- **Grafana** for dashboards  
- **Alertmanager** for notifications  

---

## Project Structure  

- **LangChainOrchestration/** → Prompt engineering, retrieval chains, context assembly  
- **ManagementScripts/** → VM provisioning, orchestration, and backups (Terraform + Ansible)  
- **Database/** → Qdrant for vectors, DuckDB for metadata  
- **EmbedGeneration/** → Embedding generation utilities  
- **Ingestion/** → SharePoint + OpenAlex pipelines  
- **Storage/** → SeaweedFS for original documents  
- **Monitoring/** → Prometheus + Grafana. Validate SeaweedFS ↔ DuckDB consistency  
- **UI/** → Streamlit & React prototypes for queries  
- **API/** → FastAPI microservice for retrieval + LLM  
- **MLExperiments/** → Fine-tuning & testing workflows  

---

## Infrastructure  

Hosted on **Proxmox** (Minisforum UM890 Pro):  
- Ryzen 9 8945HS  
- 64 GB DDR5 RAM  
- 2 TB NVMe  

---

### VM-to-Functional-Area Mapping  

Each stage of the RAG pipeline runs on a **dedicated VM**.  
This deliberate 1:1 mapping provides:  
- **Clear functional boundaries** (ingestion, embedding, storage, etc.)  
- **Fault isolation** (a failure in one stage won’t cascade)  
- **Independent scaling** (e.g., scale only embedding or inference nodes)  
- **Easier upgrades & replacements**  

| VM IP         | Hostname            | Functional Area             |
|---------------|--------------------|-----------------------------|
| 192.168.0.10  | lab-1-mgmt1        | Management & orchestration (Terraform, Ansible) |
| 192.168.0.11  | lab-1-db1          | Metadata (DuckDB) & vector DB (Qdrant) |
| 192.168.0.12  | lab-1-embed-generator | Embedding generation (OpenAI/local models) |
| 192.168.0.13  | lab-1-ingestion    | Data ingestion (SharePoint + OpenAlex pipelines) |
| 192.168.0.14  | lab-1-ui           | UI layer (Streamlit, React, TypeScript) |
| 192.168.0.15  | lab-1-api          | FastAPI microservice for retrieval, LangChain orchestration, and prompt engineering  |
| 192.168.0.16  | lab-1-PyTorch      | Local model inference (PyTorch/Mistral) |
| 192.168.0.17  | lab-1-SeaweedFS    | Distributed storage for original PDFs |
| 192.168.0.18  | lab-1-monitoring   | Prometheus, Grafana, Alertmanager |

---

This architecture makes it easy to **swap components** (e.g., different embedding models, storage backends, or UI layers) without disrupting the rest of the system.

---

## Roadmap  

- ✅ **PDF ingestion → SeaweedFS, metadata extraction → DuckDB**  
- 🔄 **Optimise project & Git structure** (monorepo setup, modular folders)  
- 🔄 **Finalise document retrieval** (Qdrant vector search + validation)  
- 🔄 **Extend ingestion** (AI, ML, and AI Ethics categories)  
- 📝 **Implement LangChain retrieval chains & dynamic prompt templates**  
- 📝 **Add React + TypeScript UI alpha**  

---
