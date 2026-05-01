# Target Discovery Copilot

Agentic copilot for drug-target discovery using public bio databases (Open Targets, ChEMBL, TCGA, PubMed).

## Stack

- **Pipelines**: Nextflow (data ingestion from bio databases)
- **Transformation**: dbt-duckdb
- **Storage**: DuckDB on local HDD, Qdrant for vector search
- **Agent**: LangGraph + NVIDIA NIM
- **Dashboard**: Streamlit / Shiny

## Setup

```bash
uv sync
cp .env.example .env  # then fill in NVIDIA_API_KEY
```

## Status

🚧 Bootstrap phase.
