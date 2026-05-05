import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

ot_raw_dir = os.environ["OT_RAW_DIR"]

conn = duckdb.connect()

print("=== SCHEMA ===")
print(conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{ot_raw_dir}/*.parquet')").fetchdf().to_string())

print("\n=== SAMPLE ROWS ===")
print(conn.execute(f"SELECT * FROM read_parquet('{ot_raw_dir}/*.parquet') LIMIT 5").fetchdf().to_string())

print("\n=== ROW COUNT ===")
print(conn.execute(f"SELECT COUNT(*) as total_rows FROM read_parquet('{ot_raw_dir}/*.parquet')").fetchdf().to_string())