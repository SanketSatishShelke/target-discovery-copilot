import os
import duckdb
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

@st.cache_resource
def get_connection():
    return duckdb.connect(os.environ["DUCKDB_PATH"], read_only=True)

@st.cache_data
def load_diseases() -> pd.DataFrame:
    conn = get_connection()
    return conn.execute("""
        SELECT disease_id, disease_name, COUNT(*) as target_count
        FROM mart_target_rankings
        GROUP BY disease_id, disease_name
        ORDER BY disease_name ASC
    """).fetchdf()

@st.cache_data
def load_targets(disease_id: str, top_n: int) -> pd.DataFrame:
    conn = get_connection()
    return conn.execute("""
        SELECT
            rank_within_disease AS rank,
            gene_symbol,
            target_id,
            ROUND(association_score, 4) AS score,
            evidence_count
        FROM mart_target_rankings
        WHERE disease_id = ?
        ORDER BY rank_within_disease
        LIMIT ?
    """, [disease_id, top_n]).fetchdf()

def render():
    diseases = load_diseases()
    diseases["label"] = diseases["disease_name"] + " (" + diseases["disease_id"] + ")"
    label_to_id = dict(zip(diseases["label"], diseases["disease_id"]))
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_label = st.selectbox(
            "Search disease by name or EFO ID",
            options=diseases["label"].tolist(),
        )
    with col2:
        top_n = st.slider("Top N targets", min_value=5, max_value=20, value=10)
    disease_id = label_to_id[selected_label]
    targets = load_targets(disease_id, top_n)
    if targets.empty:
        st.warning("No targets found for this disease.")
        return
    st.subheader(f"Top {top_n} targets — {selected_label}")
    st.dataframe(
        targets,
        width='stretch',
        hide_index=True,
        column_config={
            "rank": st.column_config.NumberColumn("Rank", width="small"),
            "gene_symbol": st.column_config.TextColumn("Gene", width="medium"),
            "target_id": st.column_config.TextColumn("Ensembl ID", width="large"),
            "score": st.column_config.NumberColumn("Score", format="%.4f", width="medium"),
            "evidence_count": st.column_config.NumberColumn("Evidence", width="small"),
        }
    )
    st.subheader("Association scores")
    st.bar_chart(targets.set_index("gene_symbol")["score"])
