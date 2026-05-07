-- dbt/models/marts/mart_target_rankings.sql
-- Final ranked drug targets per disease
-- Top 20 targets per disease, materialised as table for fast querying
-- This is the table the LangGraph agent and dashboard query directly

{{ config(materialized='table') }}

SELECT
    disease_id,
    target_id,
    association_score,
    evidence_count,
    current_novelty,
    rank_within_disease
FROM {{ ref('int_top_targets_by_disease') }}
WHERE rank_within_disease <= 20