import streamlit as st

st.set_page_config(
    page_title="Target Discovery Copilot",
    page_icon="🧬",
    layout="wide"
)

from dashboard.streamlit.pages import analytics, agent

st.title("🧬 Target Discovery Copilot")

tab1, tab2 = st.tabs(["📊 Analytics", "🤖 Agent"])

with tab1:
    analytics.render()

with tab2:
    agent.render()