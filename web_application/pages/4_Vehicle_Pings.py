import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from services.api_client import APIClient
from services.auth import require_auth
from utils.bbox import bbox_from_draw_output, format_bbox
from utils.maps import build_pings_map

require_auth()

st.title("Vehicle Pings")

if "bbox_pings" not in st.session_state:
    st.session_state["bbox_pings"] = None

with st.sidebar:
    st.subheader("Bounding box")
    default_min_lon = -68.00
    default_min_lat = 18.00
    default_max_lon = -67.00
    default_max_lat = 18.30
    min_lon = st.number_input("minLon", value=default_min_lon, format="%.6f", key="pings_min_lon")
    min_lat = st.number_input("minLat", value=default_min_lat, format="%.6f", key="pings_min_lat")
    max_lon = st.number_input("maxLon", value=default_max_lon, format="%.6f", key="pings_max_lon")
    max_lat = st.number_input("maxLat", value=default_max_lat, format="%.6f", key="pings_max_lat")
    col_apply, col_reset = st.columns(2)
    with col_apply:
        if st.button("Apply", use_container_width=True):
            st.session_state["bbox_pings"] = format_bbox((min_lon, min_lat, max_lon, max_lat))
    with col_reset:
        if st.button("Reset", use_container_width=True):
            st.session_state["bbox_pings"] = None
            for key in ["pings_min_lon", "pings_min_lat", "pings_max_lon", "pings_max_lat"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

bbox = st.session_state.get("bbox_pings")
data = APIClient().get_latest_pings(bbox=bbox) or {}
items = data.get("items") or []

st.caption(f"Showing {len(items)} vehicle pings.")

m = build_pings_map(items)
draw = st_folium(m, width=None, height=520, returned_objects=[])
new_bbox = bbox_from_draw_output(draw or {})
if new_bbox:
    st.session_state["bbox_pings"] = format_bbox(new_bbox)

df = pd.DataFrame(items)
cols = ["ping_id", "vehicle_id", "plate_number", "ts", "speed_kph", "heading_deg"]
if not df.empty:
    df = df[[c for c in cols if c in df.columns]]
st.dataframe(df, use_container_width=True)

st.divider()

# ── Add New Location Ping ──
st.subheader("Add New Location Ping")
with st.form("create_ping_form"):
    col1, col2 = st.columns(2)
    with col1:
        vehicle_id = st.number_input("Vehicle ID", min_value=1, value=1)
        ts = st.text_input("Timestamp", placeholder="2026-03-14T09:58:20")
        speed_kph = st.number_input("Speed (kph)", min_value=0.0, value=0.0)
    with col2:
        lon = st.number_input("Longitude", value=-67.1453, format="%.6f")
        lat = st.number_input("Latitude", value=18.2011, format="%.6f")
        heading_deg = st.number_input("Heading (deg)", min_value=0.0, max_value=359.9, value=0.0)
    create_submitted = st.form_submit_button("Create Ping", use_container_width=True)
    if create_submitted:
        if not ts.strip():
            st.error("Timestamp is required.")
        else:
            geom = {"type": "Point", "coordinates": [lon, lat]}
            result = APIClient().create_location_ping(
                vehicle_id, ts.strip(), geom,
                speed_kph if speed_kph > 0 else None,
                heading_deg if heading_deg > 0 else None
            )
            if result:
                st.success(f"Ping created with ID {result.get('ping_id')}!")
                st.rerun()

st.divider()

# ── Update / Delete Location Ping ──
st.subheader("Update or Delete Location Ping")

all_pings_data = APIClient().get_latest_pings() or {}
all_pings = all_pings_data.get("items") or []

if not all_pings:
    st.info("No pings available.")
else:
    ping_options = {
        f"Ping {p.get('ping_id')} — {p.get('plate_number')} @ {p.get('ts')}": p
        for p in all_pings
    }
    selected_label = st.selectbox("Select a ping", list(ping_options.keys()), key="ping_select")
    selected = ping_options[selected_label]
    selected_id = selected.get("ping_id")

    tab_update, tab_delete = st.tabs(["Update", "Delete"])

    with tab_update:
        with st.form("update_ping_form"):
            new_speed = st.number_input("Speed (kph)", min_value=0.0, value=float(selected.get("speed_kph") or 0))
            new_heading = st.number_input("Heading (deg)", min_value=0.0, max_value=359.9, value=float(selected.get("heading_deg") or 0))
            update_submitted = st.form_submit_button("Update Ping", use_container_width=True)
            if update_submitted:
                payload = {
                    "speed_kph": new_speed,
                    "heading_deg": new_heading,
                }
                result = APIClient().update_location_ping(selected_id, payload)
                if result:
                    st.success(f"Ping ID {selected_id} updated successfully!")
                    st.rerun()

    with tab_delete:
        st.warning(f"You are about to delete Ping ID {selected_id}. This cannot be undone.")
        if st.button("Confirm Delete", use_container_width=True, type="primary"):
            result = APIClient().delete_location_ping(selected_id)
            if result:
                st.success(f"Ping ID {selected_id} deleted successfully!")
                st.rerun()
