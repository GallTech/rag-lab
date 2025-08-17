## Homelab Retrieval-Augmented Generation (RAG)  

A Retrieval-Augmented Generation (RAG) system designed to ingest, embed, and query ~200,000 Artificial Intelligence research papers.

### Project Goals
1.	Hands-on learning – Build my first non-trivial Linux software project, gaining practical experience with Python, Bash, GitHub, monitoring, and related tooling.
2.	Deep dive into RAG & AI – Explore the architecture, components, and best practices of retrieval-augmented generation systems.
3.	Practical research assistant – Maintain a weekly-updated RAG pipeline of the latest AI research to both learn from and stay current with the field.

Each top-level folder represents a functional stage in the pipeline. The lab ingests ~100,000 AI research papers from **SharePoint**, **OpenAlex**, and other sources. It extracts metadata and ACLs, and generates vector embeddings for retrieval-augmented LLM reasoning. Each month I will add the latest available papers. 

- **Flexible LLM backends**: OpenAI’s ChatGPT, Google Gemini, or local models.  
- **Interchangeable components**: Ingestion, embedding, vector storage, retrieval orchestration, and LLM reasoning are decoupled.  
- **LangChain-based orchestration**: Dynamic context assembly & prompt engineering.  

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
## Retrieval Metrics

**Recall@k** - Percentage of queries where at least one relevant document appears in top-k results:

$$
Recall@k = \frac{1}{N}\sum_{i=1}^{N} \mathbb{1}[G_i \cap R_{i,k} \neq \emptyset]
$$

**Mean Reciprocal Rank (MRR@k)** - Average of reciprocal ranks of first relevant result:

$$
MRR@k = \frac{1}{N}\sum_{i=1}^{N} \frac{1}{rank_i}
$$

Where:
- $G_i$ = Set of ground truth relevant IDs for query $i$
- $R_{i,k}$ = Top-k retrieved IDs for query $i$
- $\mathbb{1}[\cdot]$ = Indicator function (1 if true, 0 otherwise)
- $rank_i$ = Position of first relevant result (∞ if none found)


## Infrastructure  

Hosted on **Proxmox** (Minisforum UM890 Pro):  
- Ryzen 9 8945HS  
- 64 GB DDR5 RAM  
- 2 TB NVMe  

### VM-to-Functional-Area Mapping  

Each stage of the RAG pipeline runs on a dedicated Ubuntu VM.  
This deliberate 1:1 mapping provides:  
- **Clear functional boundaries** (ingestion, embedding, storage, etc.)  
- **Fault isolation** (a failure in one stage won’t cascade)  
- **Independent scaling** (e.g., scale only embedding or DB nodes)  
- **Makes it easier for me to learn about and experiment with each component in isolation**  

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


## Project Timeline (2025–2027)

| Dates              | Project                          | Notes                                                                 |
|--------------------|----------------------------------|-----------------------------------------------------------------------|
| Jun – Sept 2025    | Core RAG Build (on-prem)         | Nearly complete, already processing ~200k docs                        |
| Sept – Dec 2025    | SharePoint ACL RAG               | End-to-end permission flow; changes in SharePoint must propagate fast |
| Sept – Dec 2025    | Kubernetes/Terraform/Ansible     | Refactor existing code              |
| Jan – Apr 2026     | Metrics & Golden Set             | Recall@k, MRR@k, dashboards, observability stack                      |
| May – Aug 2026     | Domain LLM (Literary)            | Train/fine-tune pipeline on curated literary corpora                  |
| Sept – Dec 2026    | Graph Retriever & Re-ranking     | Multi-hop, relationship-aware retrieval w/ Mistral-7B                 |
| Jan – Jun 2027     | Cloud Migration                  | Full pipeline → AWS/GCP; hybrid homelab ↔ cloud; metric parity check  |
| Jul – Dec 2027     | Cloud Land & Expand              | Cloud-native scaling, managed services, cost optimization             |

