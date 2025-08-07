A Retrieval-Augmented Generation (RAG) system designed to ingest, embed, and query ~100,000 Artificial Intelligence research papers.

Each top-level folder represents a functional stage in the pipeline. The lab ingests ~100,000 AI/ML/Math/Stats research papers from **SharePoint**, **OpenAlex**, and other sources. It extracts metadata and ACLs, and generates vector embeddings for retrieval-augmented LLM reasoning. 
Sub-folder structure is currently very fluid. The layout will stabalise towards the end of Sept 2025 as I approach 1.0. 

- **Flexible LLM backends**: OpenAI’s ChatGPT, Google Gemini, or local models.  
- **Interchangeable components**: ingestion, embedding, vector storage, retrieval orchestration, and LLM reasoning are decoupled.  
- **Retrieval-first design**: retrieval is separated from generation, making it easy to mix or upgrade LLMs for different tasks.  
- **LangChain-based orchestration**: dynamic context assembly & prompt engineering before LLM calls.  

Status: 🛠️ Development

The end-to-end MVP pipeline is now functional. Focus is currently on refactoring code to support unit testing and to ensure all environment variables (e.g., DB credentials, storage keys) are handled securely. Once the SharePoint ingestion process is finalised, fine-tuning work will begin (11 August 2025).

## Process Flow  

1. **Collect documents** from SharePoint and OpenAlex with metadata + ACLs  
2. **Store original PDFs in MinIO**, with metadata indexed in PostgreSQL  
3. **Chunk & embed content** Currently using a local nomic-embed-text-v1 model 
4. **Store vector representations in Qdrant** for fast similarity search  
5. **Retrieve relevant context** using **LangChain retrievers + custom Python logic**  
7. **Generate answers via pluggable LLM backend** (OpenAI, Gemini, or local models)  
8. **Serve responses** through FastAPI & Streamlit (**React + TypeScript UI under development**)  

## Monitoring  

A dedicated **monitoring server** (`lab-1-monitoring`) runs:  
- **Prometheus** for metrics collection  
- **Grafana** for dashboards  
- **Alertmanager** for notifications  

## Project Structure  

- **LangChainOrchestration/** → Prompt engineering, retrieval chains, context assembly  
- **ManagementScripts/** → VM provisioning (Terraform + Ansible), orchestration, and backups 
- **Database/** → Qdrant for vectors, PostgreSQL for metadata  
- **EmbedGeneration/** → Embedding generation utilities  
- **Ingestion/** → SharePoint + OpenAlex pipelines  
- **Storage/** → MinIO for original documents  
- **Monitoring/** → Prometheus + Grafana. Validate MinIO ↔ PostgreSQL consistency  
- **UI/** → Streamlit & React prototypes for queries  
- **API/** → FastAPI microservice for retrieval + LLM  
- **MLExperiments/** → Fine-tuning & testing workflows

## Lab Configuration Versions

This is a lab environment, where the goal is not just to build a functioning RAG pipeline, but to study and understand the impact of each component over time. While Git handles general code source control, this configuration matrix is designed to track the experimental state of each part of the system — hopefully ensuring reproducibility, meaningful comparisons, and long-term learning.

Each major pipeline script (e.g. chunking, embedding) includes a # version: tag and log execution metadata when run with the --track flag. Logged metadata includes script version, Git commit hash, and relevant configuration parameters (e.g. chunk size, splitter type, embedding model).

Each major component will have its own dedicated logging table in PostgreSQL to support analysis and reproducibility. External dependencies (e.g. embedding model, generation LLM) will be tracked manually.

This system will allow me to correlate changes in pipeline configuration with performance outcomes. I have no idea yet how to do the in an efficient and meaningful manner. My current versioning strategy is an attempt to lay the groundwork for such an approach. 

| Category             | Parameter / Element                                     | Why It Matters                                                | Current Version |
|----------------------|---------------------------------------------------------|----------------------------------------------------------------|-----------------|
| **Chunking**         | TextSplitter class (e.g. `RecursiveCharacterTextSplitter`) | Controls chunk granularity and coherence                       | 0.0.1           |
|                      | `chunk_size`, `chunk_overlap`                          | Affects semantic continuity and embedding efficiency           | 0.0.1           |
|                      | Preprocessing rules (e.g. strip `\x00`, token est.)    | Ensures clean, consistent input for chunking and embedding     | 0.0.1           |
| **Embedding**        | Current embedding model: **nomic-embed-text-v1**      | Defines the vector representation of the data                 | 0.0.1           |
|                      | Pooling strategy / device configuration                | Affects embedding consistency and performance                  | 0.0.1           |
|                      | Embedding script logic                                 | Determines batching, retry behavior, and preprocessing details | 0.0.1           |
| **Storage & Retrieval** | Qdrant config (distance metric, HNSW params, etc.)     | Impacts vector search quality and speed                        | 0.0.1           |
|                      | Collection schema (e.g. payload structure)             | Dictates how metadata is organised and queried                 | 0.0.1           |
| **Download/Filtering** | OpenAlex filtering parameters                         | Controls the scope and relevance of ingested documents         | 0.0.1           |
| **Postprocessing**   | Re-ranking strategy                                    | Modifies the ordering of retrieved results                     | 0.0.1           |
| **Retrieval Logic**  | `top_k`, similarity thresholds, reranking methods      | Strongly influences which chunks are used at inference time    | 0.0.1           |
| **Prompt Templates** | Prompt text and formatting                             | Defines how context and questions are framed                   | 0.0.1           |
| **LLM Generation**   | Generation model, temperature, top_p, etc.             | Controls response creativity, specificity, and tone            | 0.0.1           |
| **Timing**           | Chunk ingestion date filters                           | Governs incremental update behavior and data freshness         | 0.0.1           |

## Infrastructure  

Hosted on **Proxmox** (Minisforum UM890 Pro):  
- Ryzen 9 8945HS  
- 64 GB DDR5 RAM  
- 2 TB NVMe  

### VM-to-Functional-Area Mapping  

Each stage of the RAG pipeline runs on a **dedicated VM**.  
This deliberate 1:1 mapping provides:  
- **Clear functional boundaries** (ingestion, embedding, storage, etc.)  
- **Fault isolation** (a failure in one stage won’t cascade)  
- **Independent scaling** (e.g., scale only embedding or inference nodes)  
- **Easier upgrades & replacements**  
- **Makes it easier for me to learn and experiment with each component in isolation**  

| VM IP         | Hostname            | Functional Area             |
|---------------|--------------------|-----------------------------|
| 192.168.0.10  | lab-1-mgmt1        | Management & orchestration (Terraform, Ansible) |
| 192.168.0.11  | lab-1-db1          | Metadata (PostgreSQL) & vector DB (Qdrant) |
| 192.168.0.12  | lab-1-embed-generator | Embedding generation (nomic-embed-text-v1) |
| 192.168.0.13  | lab-1-ingestion    | Data ingestion (SharePoint + OpenAlex pipelines) |
| 192.168.0.14  | lab-1-ui           | UI layer (Streamlit, React, TypeScript) |
| 192.168.0.15  | lab-1-retrieval    | FastAPI microservice for retrieval, LangChain orchestration, and prompt engineering  |
| 192.168.0.16  | lab-1-PyTorch      | Local model inference (PyTorch/Mistral) |
| 192.168.0.17  | lab-1-storage01    | Object storage (MinIO) |
| 192.168.0.18  | lab-1-monitoring   | Prometheus, Grafana, Alertmanager |

This architecture makes it easy to **swap components** (e.g., different embedding models, storage backends, or UI layers) without disrupting the rest of the system. Also facilitates moving the stateless services to K8s.

## Testing Strategy  

This project evolves from **POC → MVP → Pseudo-Production**, so testing depth scales accordingly:  

- **POC (now)**  
  - Minimal sanity checks (manual or quick scripts)  
  - Focus on proving end-to-end ingestion → retrieval → generation  

- **MVP**  
  - Unit tests for key functions (chunking, embedding, metadata parsing)  
  - Basic integration tests (ingestion → MinIO → PostgreSQL → Qdrant)  
  - Simple E2E test on a small synthetic dataset  

- **Pseudo-Production**  
  - Full unit + integration test coverage  
  - E2E tests validating ingestion → storage → retrieval → generation  
  - Data integrity tests (PostgreSQL ↔ MinIO ↔ Qdrant consistency)  
  - Smoke/health checks for all services  
  - Performance tests under realistic query + ingestion load  

CI/CD will integrate **unit + integration tests** on PRs, with **nightly E2E + data validation tests** on a controlled dataset.  

## 🗓️ August Sprint  
**Start:** 1 August 2025  
**End:** 31 August 2025  

| Date         | Title                          | Description                                              | Status       |
|--------------|--------------------------------|----------------------------------------------------------|--------------|
| 2025-08-01   | Kickoff + Planning             | Define sprint goals, assign VM tasks, lock priorities    | ✅ Completed |
| 2025-08-03   | Embed Worker Sync              | Test embedding script handoff to Qdrant write queue      | 🚧 In Progress |
| 2025-08-06   | Ingestion Status Report        | Verify all OpenAlex papers ingested + stored        | ✅ Completed |
| 2025-08-08   | SharePoint ACL Audit           | Review SharePoint ingestion                        | 🔲 Not Started |
| 2025-08-11   | LangChain Chain Template Test  | Create draft RAG template                                | 🔲 Not Started |
| 2025-08-14   | Vector Consistency Validator   | Compare Qdrant IDs with chunk table in Postgres          | 🚧 In Progress |
| 2025-08-18   | CI/CD Stub Setup               | Begin draft GitHub Actions pipeline for ingest + embed   | 🔲 Not Started |
| 2025-08-21   | FastAPI Retrieval Test         | Run test query through FastAPI + LangChain orchestration | 🔲 Not Started |
| 2025-08-24   | Prometheus MinIO Alerts        | Add storage usage alerts and scrape metrics              | 🔲 Not Started |
| 2025-08-29   | Qdrant Prune & Optimize        | Remove unused vectors and optimize storage               | 🔲 Not Started |

## Roadmap  

- 🔄 **Urgent: Optimise project & Git structure**  
- 🔄 **Finalise document retrieval** (Qdrant vector search + validation)  
- 🔄 **Extend ingestion** (AI, ML, and AI Ethics categories)  
- 📝 **Implement LangChain retrieval chains & dynamic prompt templates**  
- 📝 **Build React + TypeScript UI alpha**  
- 📝 **Reprovision entire solution using Terraform and Ansible**  
- 📝 **Reprovision stateless services (API, UI, embedding workers) on Kubernetes**
- 📝 **Once that's all done, it's cloud migration time. I'll use the existing provisioning scripts and rebuild the entire thing in Azure and subsequently AWS**
