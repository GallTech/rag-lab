import os
import streamlit as st

HOST = os.getenv("UI_HOST", "0.0.0.0")
PORT = int(os.getenv("UI_PORT", "8501"))

st.set_page_config(page_title="RAG Lab UI", page_icon="🔎", layout="wide")

st.title("RAG Lab UI")
st.caption("Minimal prototype UI — Streamlit")

with st.expander("Health"):
    st.write({"status": "ok", "host": HOST, "port": PORT})

query = st.text_input("Ask about the corpus", placeholder="e.g., Transformer efficiency in small models")
if st.button("Search"):
    st.info("Wire this to Retrieval API when ready.")
