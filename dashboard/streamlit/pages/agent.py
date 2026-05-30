import streamlit as st
from agent.target_discovery_agent import run_agent
from dashboard.parsers import parse_agent_response
import concurrent.futures

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
            width="stretch",
            hide_index=True,
            column_config={
                "gene": st.column_config.TextColumn("Gene", width="medium"),
                "ensembl_id": st.column_config.TextColumn("Ensembl ID", width="large"),
                "score": st.column_config.NumberColumn("Score", format="%.2f"),
            }
        )

    for note in content.get("notes", []):
        st.caption(note)