"""
Queries DuckDB mart for all unique Ensembl target IDs, resolves them to
gene symbols via the Ensembl REST API, writes to dbt/seeds/gene_symbols.csv.

Run from project root:
    uv run python scripts/fetch_gene_symbols.py
"""

import os
import csv
import time
import requests
import duckdb
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DUCKDB_PATH = os.environ["DUCKDB_PATH"]
OUTPUT_PATH = Path(os.environ["GENE_SYMBOLS_SEED_PATH"])
ENSEMBL_API = "https://rest.ensembl.org/lookup/id"
BATCH_SIZE = 1000
RETRY_WAIT_SECONDS = 30
MAX_RETRIES = 3


def get_target_ids(db_path: str) -> list[str]:
    conn = duckdb.connect(db_path, read_only=True)
    rows = conn.execute("SELECT DISTINCT target_id FROM mart_target_rankings").fetchall()
    conn.close()
    return [r[0] for r in rows]


def resolve_batch(ensembl_ids: list[str]) -> dict[str, str]:
    payload = {"ids": ensembl_ids}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.post(ENSEMBL_API, json=payload, headers=headers, timeout=30)

        if resp.status_code == 200:
            result = {}
            for eid, info in resp.json().items():
                if info is None:
                    result[eid] = ""
                else:
                    symbol = (
                        info.get("display_name", "")
                        .split(" [")[0]
                        .strip()
                        or info.get("external_name", "")
                        or eid
                    )
                    result[eid] = symbol
            return result

        elif resp.status_code == 429:
            wait = RETRY_WAIT_SECONDS * attempt
            print(f"  Rate limited. Waiting {wait}s (attempt {attempt}/{MAX_RETRIES})...")
            time.sleep(wait)

        else:
            print(f"  Warning: HTTP {resp.status_code} — skipping batch")
            return {eid: "" for eid in ensembl_ids}

    return {eid: "" for eid in ensembl_ids}


def main():
    print(f"Connecting to DuckDB at {DUCKDB_PATH}")
    target_ids = get_target_ids(DUCKDB_PATH)
    print(f"Found {len(target_ids)} unique target IDs to resolve")

    resolved = {}
    batches = [target_ids[i:i + BATCH_SIZE] for i in range(0, len(target_ids), BATCH_SIZE)]

    for i, batch in enumerate(batches, 1):
        print(f"Resolving batch {i}/{len(batches)} ({len(batch)} IDs)...")
        resolved.update(resolve_batch(batch))
        if i < len(batches):
            time.sleep(0.5)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ensembl_id", "gene_symbol"])
        for eid, symbol in sorted(resolved.items()):
            writer.writerow([eid, symbol])

    found = sum(1 for s in resolved.values() if s and not s.startswith("ENSG"))
    print(f"\nDone. {found}/{len(target_ids)} resolved to gene symbols.")
    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()