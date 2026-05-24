import streamlit as st

from services.api_client import APIClient


def is_logged_in() -> bool:
    return st.session_state.get("user") is not None


def login(username: str, password: str) -> bool:
    client = APIClient()
    result = client.login(username, password)
    if result:
        st.session_state["user"] = result
        return True
    return False


def logout():
    st.session_state.clear()


def require_auth():
    if not is_logged_in():
        st.warning("Please log in to access this page.")
        st.stop()
