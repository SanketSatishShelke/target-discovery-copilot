import streamlit as st
from agent.target_discovery_agent import run_agent
from dashboard.parsers import parse_agent_response
import concurrent.futures

def parse_agent_response(raw: str) -> dict:
    """
    Extract structured data from agent response.
    Returns dict with keys: summary, targets (list of dicts), notes.
    """
    lines = raw.strip().split("\n")
    targets = []
    notes = []
    summary = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Match lines like: "1. APC (ENSG00000134982) — score: 0.71"
        match = re.match(r"^\d+[\.\)]\s+(\w+)\s*\(?(ENSG\d+)?\)?.*?(\d+\.\d+)", line)
        if match:
            targets.append({
                "gene": match.group(1),
                "ensembl_id": match.group(2) or "",
                "score": float(match.group(3))
            })
        elif len(targets) == 0 and len(line) > 20:
            summary = line
        else:
            notes.append(line)

    return {"summary": summary, "targets": targets, "notes": notes}


def render():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.subheader("Ask the agent")
    st.caption("Example: *What are the top targets for colorectal cancer? Use EFO_0000182.*")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                _render_agent_output(msg["content"])
            else:
                st.write(msg["content"])

    if prompt := st.chat_input("Ask about a disease or gene target..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Querying agent (this takes ~30s)..."):
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_agent, prompt)
                    raw = future.result(timeout=120)
            parsed = parse_agent_response(raw)
            _render_agent_output(parsed)
            st.session_state.messages.append({"role": "assistant", "content": parsed})


def _render_agent_output(content):
    if isinstance(content, str):
        st.write(content)
        return

    if content.get("summary"):
        st.write(content["summary"])

    if content.get("targets"):
        import pandas as pd
        df = pd.DataFrame(content["targets"])
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "gene": st.column_config.TextColumn("Gene", width="medium"),
                "ensembl_id": st.column_config.TextColumn("Ensembl ID", width="large"),
                "score": st.column_config.NumberColumn("Score", format="%.2f"),
            }
        )

    for note in content.get("notes", []):
        st.caption(note)