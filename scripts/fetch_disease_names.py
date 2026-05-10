"""
Queries DuckDB mart for all unique disease IDs, resolves them to
disease names via the Open Targets GraphQL API, writes to
dbt/seeds/disease_names.csv.

Run from project root:
    uv run python scripts/fetch_disease_names.py
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
OUTPUT_PATH = Path(os.environ["DISEASE_NAMES_SEED_PATH"])
OT_API = "https://api.platform.opentargets.org/api/v4/graphql"
BATCH_SIZE = 50        # GraphQL — smaller batches than REST
RETRY_WAIT_SECONDS = 10
MAX_RETRIES = 3

QUERY = """
query DiseaseNames($ids: [String!]!) {
  diseases(efoIds: $ids) {
    id
    name
  }
}
"""


def get_disease_ids(db_path: str) -> list[str]:
    conn = duckdb.connect(db_path, read_only=True)
    rows = conn.execute(
        "SELECT DISTINCT disease_id FROM mart_target_rankings"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def resolve_batch(disease_ids: list[str]) -> dict[str, str]:
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.post(
            OT_API,
            json={"query": QUERY, "variables": {"ids": disease_ids}},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if resp.status_code == 200:
            data = resp.json()
            diseases = data.get("data", {}).get("diseases", []) or []
            resolved = {d["id"]: d["name"] for d in diseases if d}
            # fill any not returned by API
            for did in disease_ids:
                if did not in resolved:
                    resolved[did] = ""
            return resolved

        elif resp.status_code == 429:
            wait = RETRY_WAIT_SECONDS * attempt
            print(f"  Rate limited. Waiting {wait}s (attempt {attempt}/{MAX_RETRIES})...")
            time.sleep(wait)

        else:
            print(f"  Warning: HTTP {resp.status_code} — skipping batch")
            return {did: "" for did in disease_ids}

    return {did: "" for did in disease_ids}


def main():
    print(f"Connecting to DuckDB at {DUCKDB_PATH}")
    disease_ids = get_disease_ids(DUCKDB_PATH)
    print(f"Found {len(disease_ids)} unique disease IDs to resolve")

    resolved = {}
    batches = [disease_ids[i:i + BATCH_SIZE] for i in range(0, len(disease_ids), BATCH_SIZE)]

    for i, batch in enumerate(batches, 1):
        print(f"Resolving batch {i}/{len(batches)} ({len(batch)} IDs)...")
        resolved.update(resolve_batch(batch))
        time.sleep(0.3)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["disease_id", "disease_name"])
        for did, name in sorted(resolved.items()):
            writer.writerow([did, name])

    found = sum(1 for n in resolved.values() if n)
    print(f"\nDone. {found}/{len(disease_ids)} resolved to disease names.")
    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()