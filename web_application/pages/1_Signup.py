import streamlit as st

from services.api_client import APIClient


st.title("Signup")

with st.form("signup_form"):
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm password", type="password")
    submitted = st.form_submit_button("Create account")

if submitted:
    if password != confirm:
        st.error("Passwords do not match")
    else:
        result = APIClient().signup(username, email, password)
        if result:
            st.success("Account created successfully. You can now log in.")
