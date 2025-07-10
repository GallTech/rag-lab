#!/bin/bash

echo "📊 Adding benchmarking folder..."

mkdir -p benchmarking/scripts
touch benchmarking/__init__.py
touch benchmarking/README.md
touch benchmarking/scripts/run_benchmark.py

cat <<EOF > benchmarking/README.md
# Benchmarking

This module contains tools and scripts to benchmark key stages of the RAG pipeline.

## Goals

- Measure latency and throughput of embedding, vector search, and query response.
- Track memory and CPU usage across VMs and Kubernetes services.
- Support repeatable, lightweight evaluation.

## Structure

- \`scripts/\`: Python scripts for testing and measurement
- \`run_benchmark.py\`: Example entry point

Monitoring data is visualized via Prometheus and Grafana (see \`/kubernetes/monitoring\`).
EOF

echo "✅ Benchmarking folder added at ./benchmarking"