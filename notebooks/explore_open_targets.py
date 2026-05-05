import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

duckdb_path = os.environ["DUCKDB_PATH"]

conn = duckdb.connect(duckdb_path)

print("=== VIEWS IN DATABASE ===")
print(conn.execute("SHOW TABLES").fetchdf().to_string())

print("\n=== SAMPLE FROM STAGING VIEW ===")
print(conn.execute("""
    SELECT *
    FROM main.stg_open_targets__associations
    LIMIT 5
""").fetchdf().to_string())

print("\n=== ROW COUNT ===")
print(conn.execute("""
    SELECT COUNT(*) AS total_rows
    FROM main.stg_open_targets__associations
""").fetchdf().to_string())