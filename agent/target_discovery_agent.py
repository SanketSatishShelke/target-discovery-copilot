# agent/target_discovery_agent.py
import os
import duckdb
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

load_dotenv()

# --- Tool: query the mart ---
@tool
def get_top_targets(disease_id: str, top_n: int = 10) -> str:
    """
    Get the top drug targets for a given disease EFO ID.
    Returns ranked targets with association scores and evidence counts.
    Example disease_id: EFO_0000182 (colorectal cancer)
    """
    conn = duckdb.connect(os.environ["DUCKDB_PATH"], read_only=True)
    result = conn.execute("""
        SELECT
            rank_within_disease AS rank,
            gene_symbol,
            target_id,
            ROUND(association_score, 4) AS association_score,
            evidence_count
        FROM mart_target_rankings
        WHERE disease_id = ?
        ORDER BY rank_within_disease
        LIMIT ?
    """, [disease_id, top_n]).fetchdf()
    conn.close()

    if result.empty:
        return f"No targets found for disease {disease_id}"

    return result.to_string(index=False)


@tool
def list_available_diseases(limit: int = 20) -> str:
    """
    List available disease IDs in the database.
    Use this when the user asks about a disease but doesn't know the EFO ID.
    """
    conn = duckdb.connect(os.environ["DUCKDB_PATH"], read_only=True)
    result = conn.execute("""
        SELECT DISTINCT disease_id, COUNT(*) as target_count
        FROM mart_target_rankings
        GROUP BY disease_id
        ORDER BY target_count DESC
        LIMIT ?
    """, [limit]).fetchdf()
    conn.close()
    return result.to_string(index=False)


def run_agent(question: str):
    llm = ChatOpenAI(
        model="meta/llama-3.3-70b-instruct",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ["API_KEY"],
        temperature=0,
    )

    agent = create_react_agent(
        model=llm,
        tools=[get_top_targets, list_available_diseases],
        prompt=(
            "You are a drug target discovery assistant. "
            "You help researchers identify the most promising drug targets for diseases "
            "based on Open Targets association data. "
            "Always use the tools to fetch real data before answering. "
            "When given a disease name, use list_available_diseases to find the EFO ID first."
        )
    )

    print(f"\nQuestion: {question}")
    print("-" * 60)
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    final_message = result["messages"][-1].content
    print(f"Answer: {final_message}")
    return final_message


if __name__ == "__main__":
    run_agent("What are the top 5 drug targets for colorectal cancer? Use disease ID EFO_0000182.")