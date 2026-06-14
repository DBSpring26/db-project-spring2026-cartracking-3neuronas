import os

import streamlit as st

from services.ai_client import run_assistant
from services.auth import require_auth

require_auth()

st.title("AI Assistant")
st.caption(
    "Solo responde preguntas sobre la flota: vehículos, viajes, pings, estacionamientos y tramos de carretera."
)

if not os.getenv("CURSOR_API_KEY"):
    st.error("CURSOR_API_KEY is not set. Add it to your environment or .env file.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "cursor_agent_id" not in st.session_state:
    st.session_state["cursor_agent_id"] = None

with st.sidebar:
    if st.button("Clear conversation"):
        st.session_state["messages"] = []
        st.session_state["cursor_agent_id"] = None
        st.rerun()

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pregunta sobre la flota..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    try:
        with st.spinner("Thinking..."):
            response_text, agent_id = run_assistant(
                prompt,
                st.session_state["cursor_agent_id"],
            )
        if agent_id:
            st.session_state["cursor_agent_id"] = agent_id
        st.session_state["messages"].append({"role": "assistant", "content": response_text})
    except Exception as exc:
        st.session_state["messages"].pop()
        st.error(f"Assistant error: {exc}")
        st.stop()

    st.rerun()
