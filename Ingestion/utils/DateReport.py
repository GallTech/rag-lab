#!/usr/bin/env python3
import os
import psycopg2

PG = dict(
    host=os.getenv("PG_HOST", "192.168.0.11"),
    dbname=os.getenv("PG_DB", "raglab"),
    user=os.getenv("PG_USER", "mike"),
    password=os.getenv("PG_PASSWORD"),
)

TABLE = "openalex_works"
DATE_COL_CANDIDATES = ["publication_date", "published_date"]
JSON_COL_CANDIDATES = ["data", "json", "raw", "metadata", "doc"]
JSON_DATE_KEYS = ["publication_date", "published_date", "release_date", "date"]
YEAR_COL_CANDIDATES = ["publication_year", "year"]

def q(cur, sql):
    cur.execute(sql)
    return cur.fetchall()

def main():
    if not PG["password"]:
        raise RuntimeError("PG_PASSWORD not set")

    with psycopg2.connect(**PG) as conn, conn.cursor() as cur:
        # discover columns
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
        """, (TABLE,))
        cols = {name: dtype for name, dtype in cur.fetchall()}

        # 1) direct date column?
        for c in DATE_COL_CANDIDATES:
            if c in cols:
                sql = f"""
                    SELECT to_char(date_trunc('month', {c}::date), 'YYYY-MM') AS month, COUNT(*)
                    FROM {TABLE}
                    WHERE {c} IS NOT NULL
                    GROUP BY 1
                    ORDER BY 1;
                """
                rows = q(cur, sql)
                if rows:
                    print("Month-by-month (from direct date column):")
                    for m, n in rows:
                        print(m, n)
                    return

        # 2) jsonb column + date key?
        json_cols = [c for c in JSON_COL_CANDIDATES if c in cols and "json" in cols[c]]
        for jc in json_cols:
            for jk in JSON_DATE_KEYS:
                sql = f"""
                    SELECT to_char(date_trunc('month', ({jc}->>'{jk}')::date), 'YYYY-MM') AS month, COUNT(*)
                    FROM {TABLE}
                    WHERE ({jc}->>'{jk}') IS NOT NULL
                    GROUP BY 1
                    ORDER BY 1;
                """
                try:
                    rows = q(cur, sql)
                except Exception:
                    continue
                if rows:
                    print(f"Month-by-month (from {jc}->>'{jk}'):")
                    for m, n in rows:
                        print(m, n)
                    return

        # 3) fallback: year only
        for yc in YEAR_COL_CANDIDATES:
            if yc in cols:
                sql = f"""
                    SELECT {yc} AS year, COUNT(*)
                    FROM {TABLE}
                    WHERE {yc} IS NOT NULL
                    GROUP BY 1
                    ORDER BY 1;
                """
                rows = q(cur, sql)
                if rows:
                    print("Year-only breakdown (no month-level date found):")
                    for y, n in rows:
                        print(y, n)
                    return

        print("No usable date field found in table. Check your schema.")

if __name__ == "__main__":
    main()