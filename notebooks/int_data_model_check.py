import duckdb, os
from dotenv import load_dotenv
load_dotenv()
conn = duckdb.connect(os.environ['DUCKDB_PATH'])
print(conn.execute('''
    SELECT disease_id, target_id, association_score, evidence_count, rank_within_disease
    FROM int_top_targets_by_disease
    WHERE rank_within_disease <= 3
    ORDER BY disease_id, rank_within_disease
    LIMIT 20
''').fetchdf())