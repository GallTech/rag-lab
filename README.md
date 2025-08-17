# Project Timeline (June 2025 – Dec 2027)

## June – Sept 2025 → Build Core On-Premises RAG Pipeline  
Core build: Almost complete, currently processing ~200k docs.  

## Sept – Dec 2025 → SharePoint ACL-Aware Enterprise RAG Stack  
Goal: Ensure SharePoint permissions propagate end-to-end. Any ACL change in SharePoint must rapidly percolate through the pipeline.  

## Sept – Dec 2025 → Kubernetes, Terraform and Ansible  
Tidy up and systematize existing infra work. Focus on reproducibility, automation, and deployment consistency.  

## Jan – Apr 2026 → Metrics & Golden Set Evaluation  
Introduce Recall@k, MRR@k, and dashboards. Build monitoring/observability with Prometheus, Grafana, Alertmanager.  

## May – Aug 2026 → Domain LLM Training (Literary)  
Develop training/fine-tuning pipeline on curated literary corpora.  

## Sept – Dec 2026 → Graph-Based Retriever & Re-ranking  
Implement multi-hop / relationship-aware retrieval for Mistral-7B. Add re-ranking strategies for improved precision.  

## Jan – Jun 2027 → Cloud Migration  
Migrate ingestion, embedding, retrieval, storage, UI, and monitoring to AWS/GCP. Hybrid bridge homelab ↔ cloud. Validate parity with Golden Set metrics.  

## Jul – Dec 2027 → Cloud Land & Expand  
Embrace cloud-native scaling, managed services, and cost optimization. Extend retrieval/generation features at cloud scale.  
