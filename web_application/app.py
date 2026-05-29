import streamlit as st
from services import auth
from services.api_client import APIClient

st.set_page_config(page_title="Car Tracking", page_icon="car", layout="wide")


def _login_view():
    st.title("Car Tracking System")
    st.markdown("#### Please log in to access the application.")
    st.divider()

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Please enter username and password.")
        else:
            ok = auth.login(username, password)
            if not ok:
                st.error("Invalid username or password.")
            else:
                st.rerun()

    st.divider()
    st.markdown("Don't have an account? Go to **Signup** in the sidebar.")
    st.divider()
    st.caption("CIIC 4060 / ICOM 5016 — Introduction to Database Systems | Spring 2026 | UPRM")
    st.caption("Team: Jorge Burgos · Roberto Galarza · Christian Perez")


def _app_shell():
    user = st.session_state.get("user") or {}

    with st.sidebar:
        st.markdown(f"**{user.get('username', '')}**")
        if st.button("Logout", use_container_width=True):
            auth.logout()
            st.rerun()

    st.title("Car Tracking System")
    st.markdown(f"Welcome back, **{user.get('username')}**!")
    st.divider()

    client = APIClient()

    col1, col2, col3, col4 = st.columns(4)

    vehicles_data = client.get_vehicles(limit=50) or {}
    total_vehicles = vehicles_data.get("count") or len(vehicles_data.get("items") or [])

    parking_data = client.get_parking_areas() or {}
    total_parking = parking_data.get("count") or 0

    roads_data = client.get_road_segments() or {}
    total_roads = roads_data.get("count") or 0

    pings_data = client.get_latest_pings() or {}
    total_pings = pings_data.get("count") or 0

    with col1:
        st.metric("Vehicles", total_vehicles)
    with col2:
        st.metric("Parking Areas", total_parking)
    with col3:
        st.metric("Road Segments", total_roads)
    with col4:
        st.metric("Active Pings", total_pings)

    st.divider()
    st.subheader("Quick Access")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**Parking Areas**\nView and filter parking areas on the map.")
    with c2:
        st.info("**Road Segments**\nExplore road segments with speed limits.")
    with c3:
        st.info("**Vehicle Pings**\nTrack the latest location of all vehicles.")

    c4, c5 = st.columns(2)
    with c4:
        st.info("**Breadcrumb**\nView the route of a vehicle over time.")
    with c5:
        st.info("**Dashboard**\nAnalyze ping activity over time.")

    st.divider()
    st.caption("CIIC 4060 / ICOM 5016 — Introduction to Database Systems | Spring 2026 | UPRM")
    st.caption("Team: Jorge Burgos · Roberto Galarza · Christian Perez")


if not auth.is_logged_in():
    _login_view()
else:
    _app_shell()
