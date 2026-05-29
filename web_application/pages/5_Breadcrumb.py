from datetime import datetime, time

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from services.api_client import APIClient
from services.auth import require_auth
from utils.maps import build_breadcrumb_map

require_auth()

st.title("Breadcrumb")

client = APIClient()
vehicles_data = client.get_vehicles(limit=50) or {}
vehicles = vehicles_data.get("items") or []

options = {
    f'{v.get("plate_number")} (vehicle_id={v.get("vehicle_id")})': v.get("vehicle_id")
    for v in vehicles
    if v.get("vehicle_id") is not None
}

if not options:
    st.info("No vehicles available.")
    st.stop()

label = st.selectbox("Vehicle", list(options.keys()))
vehicle_id = int(options[label])

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date")
    start_time = st.time_input("Start time", value=time(0, 0))
with col2:
    end_date = st.date_input("End date")
    end_time = st.time_input("End time", value=time(23, 59))

if st.button("Load breadcrumb"):
    from_ts = datetime.combine(start_date, start_time).isoformat()
    to_ts = datetime.combine(end_date, end_time).isoformat()
    result = client.get_breadcrumb(vehicle_id, from_ts, to_ts)
    if result:
        st.session_state["breadcrumb_result"] = result
    else:
        st.session_state["breadcrumb_result"] = None
        st.error("No breadcrumb data found for this vehicle and time range.")

if st.session_state.get("breadcrumb_result"):
    result = st.session_state["breadcrumb_result"]
    trip_ids = result.get("trip_ids") or []
    pings = result.get("pings") or []

    st.info(f"Trip IDs: {trip_ids}")

    if pings:
        m = build_breadcrumb_map(pings)
        st_folium(m, width=None, height=520)
        df = pd.DataFrame(pings)
        st.dataframe(df, width='stretch')
    else:
        st.warning("No pings found for this vehicle in the selected time range.")
