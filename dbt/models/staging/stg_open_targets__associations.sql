-- Staging model for Open Targets direct association scores
-- Source: /mnt/data/.../raw/open_targets/*.parquet
-- One row per disease-target pair

WITH source AS (
    SELECT *
    FROM read_parquet('{{ env_var("OT_RAW_DIR") }}/*.parquet')
),

renamed AS (
    SELECT
        diseaseId        AS disease_id_renamed,
        targetId         AS target_id,
        associationScore AS association_score,
        evidenceCount    AS evidence_count,
        currentNovelty   AS current_novelty
        -- timeseries excluded for now — nested struct, handled later
    FROM source
)

SELECT * FROM renamed