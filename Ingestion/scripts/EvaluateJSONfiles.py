#!/usr/bin/env python3
import os
import csv
import argparse
import psycopg2

PG_HOST = os.getenv("PG_HOST", "192.168.0.11")
PG_DB   = os.getenv("PG_DB", "raglab")
PG_USER = os.getenv("PG_USER", "mike")
PG_PASS = os.getenv("PG_PASSWORD")

# mode: "any" (uses concepts[] with score >= threshold; multi-label)
#    or "primary" (uses primary_topic only; single label per work)
SQL_ANY = r"""
WITH total AS (
  SELECT COUNT(*) AS total_works FROM openalex_works
),
exploded AS (
  SELECT
    w.id                    AS work_id,
    c->>'id'                AS concept_id,
    c->>'display_name'      AS concept_name,
    (c->>'score')::numeric  AS score
  FROM openalex_works w
  CROSS JOIN jsonb_array_elements( (w.full_raw)::jsonb->'concepts' ) AS c
),
agg AS (
  SELECT
    concept_id,
    concept_name,
    COUNT(DISTINCT work_id) FILTER (WHERE score >= %s) AS works_count
  FROM exploded
  GROUP BY concept_id, concept_name
)
SELECT
  a.concept_id,
  a.concept_name,
  a.works_count,
  t.total_works,
  CASE WHEN t.total_works > 0
       THEN ROUND(100.0 * a.works_count::numeric / t.total_works, 2)
       ELSE 0
  END AS pct_of_all
FROM agg a CROSS JOIN total t
WHERE a.works_count > 0
ORDER BY a.works_count DESC, a.concept_name ASC;
"""

SQL_PRIMARY = r"""
WITH total AS (
  SELECT COUNT(*) AS total_works FROM openalex_works
),
primary_map AS (
  SELECT
    (w.full_raw)::jsonb->'primary_topic'->>'id'           AS concept_id,
    (w.full_raw)::jsonb->'primary_topic'->>'display_name' AS concept_name
  FROM openalex_works w
),
agg AS (
  SELECT
    concept_id,
    concept_name,
    COUNT(*) AS works_count
  FROM primary_map
  WHERE concept_id IS NOT NULL
  GROUP BY concept_id, concept_name
)
SELECT
  a.concept_id,
  a.concept_name,
  a.works_count,
  t.total_works,
  CASE WHEN t.total_works > 0
       THEN ROUND(100.0 * a.works_count::numeric / t.total_works, 2)
       ELSE 0
  END AS pct_of_all
FROM agg a CROSS JOIN total t
ORDER BY a.works_count DESC, a.concept_name ASC;
"""

def run_query(conn, mode, threshold):
    with conn.cursor() as cur:
        if mode == "any":
            cur.execute(SQL_ANY, (threshold,))
        else:
            cur.execute(SQL_PRIMARY)
        return cur.fetchall(), [d.name for d in cur.description]

def main():
    ap = argparse.ArgumentParser(description="Concept coverage report from Postgres (all concepts).")
    ap.add_argument("--mode", choices=["any","primary"], default="any",
                    help="'any' = concepts[] with score >= threshold (multi-label); 'primary' = primary_topic only.")
    ap.add_argument("--threshold", type=float, default=0.4,
                    help="Concept score cutoff for 'any' mode (default 0.4). Ignored in 'primary' mode.")
    ap.add_argument("--top", type=int, default=25, help="Show top N rows in console (default 25).")
    ap.add_argument("--output", default="concept_coverage_report.csv",
                    help="Output CSV path (default: concept_coverage_report.csv)")
    ap.add_argument("--host", default=PG_HOST)
    ap.add_argument("--db",   default=PG_DB)
    ap.add_argument("--user", default=PG_USER)
    ap.add_argument("--password", default=PG_PASS)
    args = ap.parse_args()

    if not args.password:
        raise RuntimeError("❌ PG_PASSWORD not set (env) or --password not provided.")

    conn = psycopg2.connect(host=args.host, dbname=args.db, user=args.user, password=args.password)
    try:
        rows, cols = run_query(conn, args.mode, args.threshold)

        # Console summary
        mode_str = "ANY (multi-label, score>=%.2f)" % args.threshold if args.mode=="any" \
                   else "PRIMARY_TOPIC (single label)"
        print(f"\n--- Concept Coverage Report (mode: {mode_str}) ---")
        print(f"Total concepts matched: {len(rows)}")
        print(f"Showing top {min(args.top, len(rows))}:\n")

        print(f"{'Rank':>4}  {'Works':>8}  {'% of all':>8}  Concept")
        for i, r in enumerate(rows[:args.top], 1):
            concept_id, concept_name, works_count, total_works, pct = r
            print(f"{i:>4}  {works_count:>8}  {pct:>8.2f}  {concept_name}  ({concept_id})")

        # CSV output
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["concept_id","concept_name","works_count","total_works","pct_of_all","mode","threshold"])
            for concept_id, concept_name, works_count, total_works, pct in rows:
                w.writerow([concept_id, concept_name, works_count, total_works, f"{pct:.2f}", args.mode,
                            args.threshold if args.mode=="any" else "n/a"])

        print(f"\n💾 CSV written to: {args.output}")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
