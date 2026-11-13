"""Streamlit chat UI.   Run:  streamlit run app.py"""
import os
import uuid

import streamlit as st

from copilot import config

st.set_page_config(page_title="AI Governance Copilot", page_icon=":material/shield:", layout="centered")

st.title("AI Governance Copilot")
st.caption("An agentic RAG assistant for ISO/IEC 42001, the EU AI Act and AI risk work. "
           "Built with LangGraph, LangChain, Qdrant, FastEmbed, guardrails, evals and MCP.")

with st.sidebar:
    st.subheader("What it can do")
    st.markdown("- Answer governance questions with **cited sources** (RAG)\n"
                "- **Classify** an AI use case into a risk tier\n"
                "- **Draft** a risk-register entry\n"
                "- Block prompt injection and **redact personal data**")
    st.subheader("Under the hood")
    st.markdown(f"- LLM: `{config.MODEL}`\n- Embeddings: `{config.EMBEDDING_MODEL}`\n"
                "- Vector DB: Qdrant (in memory)\n- Orchestration: LangGraph")
    if st.button("New conversation", icon=":material/refresh:"):
        st.session_state.clear()
        st.rerun()

# On Streamlit Cloud, copy the key from Secrets into the environment if needed
# (also handles a key placed under a [section] heading in the Secrets box).
try:
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        value = st.secrets.get(name) or next(
            (sec[name] for sec in st.secrets.values() if hasattr(sec, "get") and sec.get(name)), None)
        if value and not os.getenv(name):
            os.environ[name] = str(value).strip()
except Exception:  # no secrets file (e.g. running locally with .env)
    pass

if not config.has_llm_key():
    st.warning("No Gemini API key found. Get a free key at https://aistudio.google.com/apikey "
               "and add `GOOGLE_API_KEY` to `.env` (local) or to the app's Secrets (Streamlit Cloud).")
    st.stop()


@st.cache_resource(show_spinner="Loading knowledge base and agent (first run takes ~30 s)...")
def load_agent():
    from copilot.agent import build_graph
    from copilot.knowledge import get_knowledge_base
    get_knowledge_base()  # embed the documents once, at start-up
    return build_graph()


graph = load_agent()
from copilot.agent import run_turn  # noqa: E402  (imported after the heavy load above)

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.history = []

EXAMPLES = [
    "What are the nine control areas in ISO/IEC 42001 Annex A?",
    "We use AI to screen CVs for hiring in Germany. What risk tier is that and what must we do?",
    "Draft a risk-register entry for our loan chatbot giving wrong interest rates, likelihood 3, impact 4.",
    "What does India's DPDP Act require, and by when?",
]

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        if turn.get("trace"):
            with st.expander("How I got this answer"):
                st.json(turn["trace"])

prompt = st.chat_input("Ask about AI governance...")
if not st.session_state.history:
    st.write("**Try one:**")
    for example in EXAMPLES:
        if st.button(example, use_container_width=True):
            prompt = example

if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = run_turn(graph, prompt, st.session_state.thread_id)
            except Exception as error:  # show a helpful message instead of a stack trace
                st.error(f"The model call failed: {error}\n\nIf the model name is not found or "
                         "the free quota is used up, set MODEL (e.g. `google_genai:gemini-2.5-flash`) "
                         "in your secrets and retry in a minute.")
                st.stop()
        st.markdown(result["answer"])
        trace = {k: result[k] for k in ("tools_used", "sources", "guard_events", "blocked", "latency_s")}
        with st.expander("How I got this answer"):
            st.json(trace)
    st.session_state.history.append({"role": "assistant", "content": result["answer"], "trace": trace})
