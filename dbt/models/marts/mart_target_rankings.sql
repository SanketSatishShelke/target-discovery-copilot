-- dbt/models/marts/mart_target_rankings.sql
-- Final ranked drug targets per disease
-- Top 20 targets per disease, materialised as table for fast querying
-- This is the table the LangGraph agent and dashboard query directly

{{ config(materialized='table') }}

WITH ranked AS (
    SELECT * FROM {{ ref('int_top_targets_by_disease') }}
),

gene_names AS (
    SELECT ensembl_id, gene_symbol FROM {{ ref('gene_symbols') }}
),

disease_names AS (
    SELECT disease_id, disease_name FROM {{ ref('disease_names') }}
)

SELECT
    r.disease_id,
    COALESCE(d.disease_name, r.disease_id) AS disease_name,
    r.target_id,
    COALESCE(g.gene_symbol, r.target_id) AS gene_symbol,
    r.association_score,
    r.evidence_count,
    r.current_novelty,
    r.rank_within_disease
FROM ranked r
LEFT JOIN gene_names g ON r.target_id = g.ensembl_id
LEFT JOIN disease_names d ON r.disease_id = d.disease_id
WHERE r.rank_within_disease <= 20
ORDER BY r.disease_id, r.rank_within_disease