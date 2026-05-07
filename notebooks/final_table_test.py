import duckdb, os
from dotenv import load_dotenv
load_dotenv()
conn = duckdb.connect(os.environ['DUCKDB_PATH'])
print(conn.execute('''
    SELECT disease_id, target_id, association_score, evidence_count, rank_within_disease
    FROM mart_target_rankings
    WHERE disease_id = 'EFO_0000182'
    ORDER BY rank_within_disease
''').fetchdf())