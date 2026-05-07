-- dbt/models/intermediate/int_top_targets_by_disease.sql
-- For each disease, rank all associated targets by association score
-- Only include associations with meaningful evidence

WITH ranked AS (
    SELECT
        disease_id,
        target_id,
        association_score,
        evidence_count,
        current_novelty,
        RANK() OVER (
            PARTITION BY disease_id
            ORDER BY association_score DESC
        ) AS rank_within_disease
    FROM {{ ref('stg_open_targets__associations') }}
    WHERE association_score > 0.1
      AND evidence_count > 2
)

SELECT * FROM ranked