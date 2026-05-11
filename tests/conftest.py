import os
import pytest
import duckdb


@pytest.fixture
def mart_db(tmp_path):
    """
    In-memory DuckDB with a mart_target_rankings table populated with
    minimal realistic data. No file I/O, no external services.

    tmp_path is a pytest built-in fixture -- gives you a fresh temp
    directory per test. We use it so DUCKDB_PATH env var points somewhere
    real (duckdb.connect needs a path or ':memory:').
    """
    db_path = str(tmp_path / "test.duckdb")
    conn = duckdb.connect(db_path)

    conn.execute("""
        CREATE TABLE mart_target_rankings (
            disease_id          VARCHAR,
            disease_name        VARCHAR,
            target_id           VARCHAR,
            gene_symbol         VARCHAR,
            association_score   DOUBLE,
            evidence_count      BIGINT,
            current_novelty     DOUBLE,
            rank_within_disease INTEGER
        )
    """)

    conn.execute("""
        INSERT INTO mart_target_rankings VALUES
            ('EFO_1001951', 'colorectal carcinoma', 'ENSG00000134982', 'APC',   0.7217, 42, 0.5, 1),
            ('EFO_1001951', 'colorectal carcinoma', 'ENSG00000141736', 'ERBB2', 0.4217, 38, 0.4, 2),
            ('EFO_1001951', 'colorectal carcinoma', 'ENSG00000012048', 'BRCA1', 0.3100, 20, 0.3, 3),
            ('EFO_0000181', 'breast carcinoma',     'ENSG00000141736', 'ERBB2', 0.9100, 99, 0.8, 1),
            ('EFO_0000181', 'breast carcinoma',     'ENSG00000012048', 'BRCA1', 0.8800, 88, 0.7, 2)
    """)

    conn.close()

    # Set env var so the tool functions can find the DB via os.environ
    os.environ["DUCKDB_PATH"] = db_path
    yield db_path

    # Cleanup: unset env var after test so tests don't bleed into each other
    del os.environ["DUCKDB_PATH"]