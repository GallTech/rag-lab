#!/usr/bin/env bash
# pg_health.sh — compact Postgres health report
# Usage:
#   ./pg_health.sh                      # uses env/defaults
#   PGDATABASE=raglab PGUSER=postgres ./pg_health.sh
#   ./pg_health.sh -h 192.168.0.11 -p 5432 -d raglab -U postgres
#
# Notes:
# - Requires: psql and (optionally) the pg_stat_statements extension
# - Set CHUNKS_TABLE (default: chunks) and FETCH_LIMIT (default: 1000) for the EXPLAIN

set -euo pipefail

# ---- Config (overridable via env or flags) ----
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGDATABASE="${PGDATABASE:-raglab}"
PGUSER="${PGUSER:-postgres}"
FETCH_LIMIT="${FETCH_LIMIT:-1000}"
CHUNKS_TABLE="${CHUNKS_TABLE:-chunks}"

# ---- Flags ----
while getopts ":h:p:d:U:" opt; do
  case $opt in
    h) PGHOST="$OPTARG" ;;
    p) PGPORT="$OPTARG" ;;
    d) PGDATABASE="$OPTARG" ;;
    U) PGUSER="$OPTARG" ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 2 ;;
  esac
done

PSQL="psql -X -h ${PGHOST} -p ${PGPORT} -d ${PGDATABASE} -U ${PGUSER} -v ON_ERROR_STOP=1"

hr() { printf '%*s\n' "${COLUMNS:-80}" '' | tr ' ' '-'; }

echo "== PostgreSQL Health Report =="
echo "Target: host=${PGHOST} db=${PGDATABASE} user=${PGUSER} port=${PGPORT}"
hr

# 0) Runtime basics
echo ">> Runtime basics"
$PSQL -Atqc "SELECT version();"
$PSQL -Atqc "SHOW shared_preload_libraries;"
$PSQL -Atqc "SHOW track_io_timing;"
$PSQL -Atqc "SELECT pg_postmaster_start_time();"
hr

# 1) Global cache hit ratio
echo ">> Global cache hit ratio"
$PSQL -c "SELECT round(sum(blks_hit)*100/nullif(sum(blks_hit)+sum(blks_read),0),2) AS cache_hit_pct
          FROM pg_stat_database;"
hr

# 2) Per-database cache ratios (top readers first)
echo ">> Per-database cache ratios"
$PSQL -c "SELECT datname,
                 blks_hit, blks_read,
                 ROUND(blks_hit*100.0/NULLIF(blks_hit+blks_read,0),2) AS hit_pct
          FROM pg_stat_database
          ORDER BY blks_read DESC;"
hr

# 3) Table-level IO hot spots (user tables)
echo ">> Table-level IO (pg_statio_user_tables) — top 15 by heap reads"
$PSQL -c "SELECT relname,
                 heap_blks_read, heap_blks_hit,
                 ROUND(heap_blks_hit*100.0/NULLIF(heap_blks_hit+heap_blks_read,0),2) AS hit_pct
          FROM pg_statio_user_tables
          ORDER BY heap_blks_read DESC
          LIMIT 15;"
hr

# 4) Index-level IO hot spots (user indexes)
echo ">> Index-level IO (pg_statio_user_indexes) — top 15 by index reads"
$PSQL -c "SELECT relname, indexrelname,
                 idx_blks_read, idx_blks_hit,
                 ROUND(idx_blks_hit*100.0/NULLIF(idx_blks_hit+idx_blks_read,0),2) AS hit_pct
          FROM pg_statio_user_indexes
          ORDER BY idx_blks_read DESC
          LIMIT 15;"
hr

# 5) Slowest queries (pg_stat_statements), if available
HAS_PGSS="$($PSQL -Atqc "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='pg_stat_statements');")"
if [[ "$HAS_PGSS" == "t" ]]; then
  echo ">> Slowest queries (pg_stat_statements) — top 10 by mean_exec_time"
  $PSQL -c "SELECT round(mean_exec_time,2) AS mean_ms,
                   calls,
                   CASE WHEN length(query) > 120 THEN substr(query,1,117)||'...' ELSE query END AS query
            FROM pg_stat_statements
            WHERE calls > 0
            ORDER BY mean_exec_time DESC
            LIMIT 10;"
else
  echo ">> Slowest queries: pg_stat_statements not installed on ${PGDATABASE} (skipping)"
fi
hr

# 6) Chunk fetch query — EXPLAIN ANALYZE (adjust CHUNKS_TABLE/FETCH_LIMIT as needed)
echo ">> EXPLAIN ANALYZE (BUFFERS) for chunk fetch"
$PSQL -c "EXPLAIN (ANALYZE, BUFFERS, WAL, SUMMARY)
          SELECT id, work_id, text
          FROM ${CHUNKS_TABLE}
          WHERE embedded = FALSE
          ORDER BY created_at
          LIMIT ${FETCH_LIMIT};"
hr

echo "Done."
