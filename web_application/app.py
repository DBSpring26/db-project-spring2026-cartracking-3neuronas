import streamlit as st

from services import auth


st.set_page_config(page_title="Car Tracking", layout="wide")


def _login_view():
    st.title("Car Tracking")
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        ok = auth.login(username, password)
        if not ok:
            st.error("Login failed")
        else:
            st.rerun()


def _app_shell():
    user = st.session_state.get("user") or {}
    st.sidebar.success(f"Welcome, {user.get('username')}")
    if st.sidebar.button("Logout"):
        auth.logout()
        st.rerun()
    st.title("Car Tracking")
    st.write("Use the pages on the left to navigate.")


if not auth.is_logged_in():
    _login_view()
else:
    _app_shell()
