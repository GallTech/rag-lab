# VM Resource Policy — CPU + **Memory** Tiers

This extends the CPU tiering with **RAM rules** that keep core services steady while allowing headroom for batch work.

---

## Memory Tiers

### **Tier A — Batch / Hog (embedding, heavy training)**
- **Goal:** Run fast, but yield memory gracefully if others need it.
- **Max RAM (`--memory`):** 28–32 GB
- **Min RAM (`--balloon`):** 18–22 GB
- **Ballooning:** **Enabled** (min set as above)
- **Swap (guest):** modest (2–4 GB); `vm.swappiness=10–20`
- **Notes:** Embedding is bursty; a healthy min prevents GC/alloc churn, ballooning returns idle memory.

### **Tier B — Active Services (DB, ingestion, retrieval)**
- **Goal:** Stay responsive; avoid paging.
- **DB**
  - **Max RAM:** 16–24 GB
  - **Min RAM:** 14–20 GB
  - **Ballooning:** Prefer **Disabled** for Postgres **or** set a **high min** (≥ 85% of max)
  - **Swap (guest):** small; `vm.swappiness=1–10`
  - **DB tuning:** `shared_buffers ≈ 25% RAM`, watch `work_mem`.
- **Ingestion / Retrieval**
  - **Max RAM:** 8–16 GB
  - **Min RAM:** 6–12 GB
  - **Ballooning:** **Enabled**
  - **Swap (guest):** small; `vm.swappiness=10–20`

### **Tier C — Baseline (mgmt, ui, monitoring, storage, idle train)**
- **Goal:** Be frugal; burst when needed.
- **Max RAM:** 2–4 GB
- **Min RAM:** 1.5–3 GB (match max if tiny)
- **Ballooning:** **Enabled**
- **Swap (guest):** default is fine; `vm.swappiness=30–60`

---

## Current Fleet — Suggested Memory Settings

| VMID | Name                   | Tier | vCPU | **Max RAM** | **Min RAM (balloon)** | Notes |
|-----:|------------------------|:----:|:----:|------------:|----------------------:|------|
| 9103 | lab-1-embed01          |  A   | 14   | 28–32 GB    | 18–22 GB              | Enable ballooning (currently 0) |
| 9102 | lab-1-db01             |  B   | 4    | 16–24 GB    | 14–20 GB              | Prefer balloon **off** for PG, or min ≥85% |
| 9104 | lab-1-ingestion01      |  B   | 4    | 12–16 GB    | 8–12 GB               | Balloon on |
| 9106 | lab-1-retrieval01      |  B   | 4    | 12–16 GB    | 8–12 GB               | Balloon on |
| 9101 | lab-1-mgmt01           |  C   | 2    | 4–6 GB      | 3–5 GB                | If mostly idle, 4/3 is fine |
| 9105 | lab-1-ui01             |  C   | 2    | 2–4 GB      | 2–3 GB                | Web UI is light |
| 9107 | lab-1-train01          |  C   | 2    | 2–4 GB      | 2–3 GB                | Placeholder until real training |
| 9108 | lab-1-storage01        |  C   | 2    | 4–6 GB      | 3–5 GB                | I/O bound |
| 9109 | lab-1-monitoring01     |  C   | 2    | 2–4 GB      | 2–3 GB                | If Prom/Grafana: 4/3 can help |

> Rule of thumb: **Tier B (DB)** either disables ballooning or sets **high min**. Others keep ballooning **on** with sensible mins.

---

## Proxmox Commands (examples)

### Set memory + ballooning
```bash
# Tier A (embed)
qm set 9103 --memory 28672 --balloon 20480

# Tier B (db: balloon off)
qm set 9102 --memory 16384 --balloon 0        # disables ballooning for stability

# Tier B (ingestion/retrieval: balloon on)
qm set 9104 --memory 16384 --balloon 12288
qm set 9106 --memory 16384 --balloon 12288

# Tier C (baseline)
qm set 9101 --memory 6144  --balloon 5120
qm set 9105 --memory 4096  --balloon 3072
qm set 9107 --memory 4096  --balloon 3072
qm set 9108 --memory 6144  --balloon 5120
qm set 9109 --memory 4096  --balloon 3072
