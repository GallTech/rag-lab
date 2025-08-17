## Homelab Retrieval-Augmented Generation (RAG)  

A Retrieval-Augmented Generation (RAG) system designed to ingest, embed, and query ~200,000 Artificial Intelligence research papers.

### Project Goals
1.	Hands-on learning – Build my first non-trivial Linux software project, gaining practical experience with Python, Bash, GitHub, monitoring, and related tooling.
2.	Deep dive into RAG & AI – Explore the architecture, components, and best practices of retrieval-augmented generation systems.
3.	Practical research assistant – Maintain a weekly-updated repository of the latest AI research, enriched through my RAG pipeline and queried via LLMs.

The lab ingests ~200,000 AI research papers from **SharePoint**, **OpenAlex**, and other sources. It extracts metadata and ACLs, and generates vector embeddings for retrieval-augmented LLM reasoning. Each month I will add the latest available papers. 

- **Flexible LLM backends**: OpenAI’s ChatGPT, Google Gemini, or local models.  
- **Interchangeable components**: Ingestion, embedding, vector storage, retrieval orchestration, and LLM reasoning are decoupled.  
- **LangChain-based orchestration**: Dynamic context assembly & prompt engineering.  

## Project Structure  

Each functional stage of the pipeline has:  
- a **folder** in the repository (code & configs)  
- a **dedicated Git branch** (isolated development)  
- a **dedicated VM** (runtime environment)  

This **1:1:1 mapping** enforces clear separation of concerns and makes it easy to evolve, test, or swap out stages independently. As I move forward, this will evolve to a more standard feature-branching workflow within each service branch.  

| VM Name              | Branch Name              | Description                                                      |
|----------------------|--------------------------|------------------------------------------------------------------|
| lab-1-mgmt1          | lab-1-mgmt1              | Management & orchestration (Terraform, Ansible, backups)         |
| lab-1-db1            | lab-1-db1                | Metadata (PostgreSQL) + Vector DB (Qdrant)                       |
| lab-1-embed-generator| lab-1-embed-generator    | Local model: nomic-embed-text-v1                       |
| lab-1-ingestion      | lab-1-ingestion          | Data ingestion (SharePoint + OpenAlex pipelines)                 |
| lab-1-ui             | lab-1-ui                 | UI layer (Streamlit, React, TypeScript)                          |
| lab-1-retrieval      | lab-1-retrieval          | FastAPI retrieval microservice + LangChain orchestration         |
| lab-1-storage01      | lab-1-storage01          | Object storage (MinIO)                                           |
| lab-1-monitoring     | lab-1-monitoring         | Monitoring stack (Prometheus, Grafana, Alertmanager)             |
| lab-1-db2            | lab-1-db2                | Secondary DB node (replication/backup testing)                   |


## Retrieval Metrics
These metrics run in the evaluation pipeline (Metrics & Golden Set stage) to measure how well the retriever (Qdrant + re-ranking) surfaces relevant documents, independent of the LLM.

As I experiment with RAG pipelines, the challenge is tracing how changes to each stage affect overall performance. Metrics like these provide a starting point for systematically measuring and comparing those impacts.

**Precision@k** - Fraction of retrieved documents that are relevant:

$$
Precision@k = \frac{1}{N}\sum_{i=1}^{N} \frac{|G_i \cap R_{i,k}|}{k}
$$

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
- $|\cdot|$ = Cardinality of set


## Infrastructure  

Hosted on **Proxmox** (Minisforum UM890 Pro):  
- Ryzen 9 8945HS  
- 64 GB DDR5 RAM  
- 2 TB NVMe  

## Project Timeline (2025–2027)

| Dates              | Project                          | Notes                                                                 |
|--------------------|----------------------------------|-----------------------------------------------------------------------|
| Jun – Aug 2025     | Core RAG Build (on-prem)         | Nearly complete, already processing ~200k docs                        |
| Sept – Dec 2025    | SharePoint ACL RAG               | End-to-end permission flow; changes in SharePoint must propagate fast |
| Sept – Dec 2025    | Kubernetes/Terraform/Ansible     | Refactor existing code              |
| Jan – Apr 2026     | Metrics & Golden Set             | Optimise dashboards & observability stack                      |
| May – Aug 2026 | Domain LLM (AI Research) | Fine-tune pipeline on AI/ML research corpora; experiment with domain-adapted summarisation & retrieval |
| Sept – Dec 2026    | Graph Retriever & Re-ranking     | Multi-hop, relationship-aware retrieval with Mistral-7B                 |
| Jan – Jun 2027     | Cloud Migration                  | Full pipeline → AWS/GCP; hybrid homelab ↔ cloud; metric parity check  |
| Jul – Dec 2027     | Cloud Land & Expand              | Cloud-native scaling, managed services, cost optimization             |

