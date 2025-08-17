## Homelab Retrieval-Augmented Generation (RAG)  

A Retrieval-Augmented Generation (RAG) system designed to ingest, embed, and query ~200,000 Artificial Intelligence research papers.

1.	Hands-on learning – Build my first non-trivial Linux software project, gaining practical experience with Python, Bash, GitHub, monitoring, and related tooling.
2.	Deep dive into RAG & AI – Explore the architecture, components, and best practices of retrieval-augmented generation systems.
3.	Practical research assistant – Maintain a weekly-updated RAG pipeline of the latest AI research to both learn from and stay current with the field.

Each top-level folder represents a functional stage in the pipeline. The lab ingests ~100,000 AI/ML/Math/Stats research papers from **SharePoint**, **OpenAlex**, and other sources. It extracts metadata and ACLs, and generates vector embeddings for retrieval-augmented LLM reasoning. 
Sub-folder structure is currently very fluid. The layout will stabalise towards the end of Sept 2025 as I approach 1.0. 

- **Flexible LLM backends**: OpenAI’s ChatGPT, Google Gemini, or local models.  
- **Interchangeable components**: ingestion, embedding, vector storage, retrieval orchestration, and LLM reasoning are decoupled.  
- **LangChain-based orchestration**: dynamic context assembly & prompt engineering.  

Status: 🛠️ Development

The end-to-end MVP pipeline is now functional. Focus is currently on refactoring code to support unit testing and to ensure all environment variables (e.g., DB credentials, storage keys) are handled securely. Once the SharePoint ingestion process is finalised, fine-tuning work will begin (11 August 2025).

## Process Flow  

1. **Collect documents** from SharePoint and OpenAlex with metadata + ACLs  
2. **Store original PDFs in MinIO**, with metadata indexed in PostgreSQL  
3. **Chunk & embed content** Currently using a local nomic-embed-text-v1 model 
4. **Store vector representations in Qdrant** for fast similarity search  
5. **Retrieve relevant context** using **LangChain retrievers + custom Python logic**  
6. **Generate answers via pluggable LLM backend** (OpenAI, Gemini, or local models)  
7. **Serve responses** through FastAPI & Streamlit (**React + TypeScript UI under development**)  

## Monitoring  

A dedicated **monitoring server** (`lab-1-monitoring`) runs Node Exporter + Prometheus + Grafana 

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

Each major pipeline script (e.g. chunking, embedding) includes a # version: tag and logs execution metadata when run with the --track flag. Logged metadata includes script version, Git commit hash, and relevant configuration parameters (e.g. chunk size, splitter type, embedding model).

Each major component will have its own dedicated run logging table in PostgreSQL to support analysis and reproducibility. External dependencies (e.g. embedding model, generation LLM) will be tracked manually. A basic reporting script queries the logs in PostgreSQL (chunking, embedding, retrieval, etc.), and outputs Markdown reports into my local Obsidian vault for this project.

This system will allow me to correlate changes in pipeline configuration with performance outcomes. I have no idea yet how to do this in an efficient and meaningful manner. I'll track progress using subjective metrics and attempt to isolate hard date such as Recall@k. My current configuration versioning work is an attempt to lay the groundwork for such an approach. 

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


## Weekly Golden Set Evaluation  

To track retrieval quality over time, the lab maintains a **golden set** of ~100 curated Q→A pairs with known relevant document or chunk IDs.  
I run these queries through an offline harness against the retriever with no LLM, logging Recall@k and MRR@k into Postgres for Grafana trend analysis. This tests the sytems's ability to find the relevant info, and not the LLM's ability to pull it all together.   

**Recall@k** – % of queries where at least one gold item appears in the top-k results:  

`Recall@k = (1/N) Σ[i=1→N]  1[ Gᵢ ∩ Rᵢ,k ≠ ∅ ]`  

**MRR@k** – Mean reciprocal rank of the first correct hit:  

`MRR@k = (1/N) Σ[i=1→N]  1 / rankᵢ`  

Where:  

- `Gᵢ` = set of gold IDs for query `i`  
- `Rᵢ,k` = top-k retrieved IDs for query `i`  
- `1[...]` = indicator function (1 if condition is true, else 0)  
- `rankᵢ` = position of the first relevant result, or 0 if none found  

This ensures parameter changes, embedding swaps, and retriever tweaks can be objectively tracked.

Since high Recall@k doesn’t guarantee good answers, in the next sprint (Sept 2025), I plan to include end-to-end evaluation of generation quality to complement the existing retrieval metrics. While Recall@k and MRR@k are excellent for assessing the retriever, this next phase will focus on the quality of the final, LLM-generated answer. This will involve extending the weekly Golden Set Evaluation to include not just correct document IDs, but also canonical or 'ideal' answers. 

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
- **Independent scaling** (e.g., scale only embedding or DB nodes)  
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

# Project Timeline (Sept 2025 – June 2027)

## Main Projects

1. **Baseline RAG**  
   Dates: → Sept 2025  
   Focus: End-to-end ingestion → retrieval → LLM  

2. **ACL-Aware Enterprise RAG Stack**  
   Dates: Sept 2025 – Jan 2026  
   Focus: Security, governance, compliance, integrations  

3. **Metrics & Golden Set Evaluation**  
   Dates: Jan – Jun 2026  
   Focus: Recall@k, MRR@k, dashboards, bed down RAG  

4. **Domain LLM Training (Literary)**  
   Dates: Jul – Dec 2026  
   Focus: Training/fine-tuning pipeline on custom corpora  

5. **Graph-Based Retriever**  
   Dates: Jan – Jun 2027  
   Focus: Multi-hop / relationship-aware retrieval for Mistral-7B  

---

## Parallel Workstream: Deployment & Ops

- **Continuous CI/CD improvement**  
- **Kubernetes orchestration** (Helm charts, HPA, service mesh)  
- **Terraform infrastructure as code**  
- **Ansible automation** (config mgmt, secrets, backups)  
- **Monitoring & observability** (Prometheus, Grafana, Alertmanager)  
- **Cloud migration modules** (AWS/GCP)  
