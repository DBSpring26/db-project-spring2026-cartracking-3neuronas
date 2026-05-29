import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from services.api_client import APIClient
from services.auth import require_auth
from utils.bbox import bbox_from_draw_output, format_bbox
from utils.maps import build_roads_map

require_auth()

st.title("Road Segments")

if "bbox_roads" not in st.session_state:
    st.session_state["bbox_roads"] = None

with st.sidebar:
    st.subheader("Bounding box")
    default_min_lon = -67.14
    default_min_lat = 18.20
    default_max_lon = -67.12
    default_max_lat = 18.22
    min_lon = st.number_input("minLon", value=default_min_lon, format="%.6f", key="roads_min_lon")
    min_lat = st.number_input("minLat", value=default_min_lat, format="%.6f", key="roads_min_lat")
    max_lon = st.number_input("maxLon", value=default_max_lon, format="%.6f", key="roads_max_lon")
    max_lat = st.number_input("maxLat", value=default_max_lat, format="%.6f", key="roads_max_lat")
    col_apply, col_reset = st.columns(2)
    with col_apply:
        if st.button("Apply", use_container_width=True):
            st.session_state["bbox_roads"] = format_bbox((min_lon, min_lat, max_lon, max_lat))
    with col_reset:
        if st.button("Reset", use_container_width=True):
            st.session_state["bbox_roads"] = None
            for key in ["roads_min_lon", "roads_min_lat", "roads_max_lon", "roads_max_lat"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

bbox = st.session_state.get("bbox_roads")
data = APIClient().get_road_segments(bbox=bbox) or {}
items = data.get("items") or []

st.caption(f"Showing {len(items)} road segments.")

m = build_roads_map(items)
draw = st_folium(m, width=None, height=520, returned_objects=[], key="roads_map")

new_bbox = bbox_from_draw_output(draw or {})
if new_bbox:
    st.session_state["bbox_roads"] = format_bbox(new_bbox)

df = pd.DataFrame(items)
cols = ["road_id", "name", "speed_limit_kph", "created_at"]
if not df.empty:
    df = df[[c for c in cols if c in df.columns]]
st.dataframe(df, use_container_width=True)

st.divider()
st.subheader("Add New Road Segment")

with st.form("create_road_form"):
    name = st.text_input("Name", placeholder="e.g. PR-2 Segment A")
    speed_limit_kph = st.number_input("Speed limit (kph)", min_value=0, value=0)
    is_oneway = st.checkbox("One way")
    direction = st.selectbox("Direction", ["both", "forward"])
    coords_input = st.text_area(
        "Coordinates (one lon,lat per line)",
        placeholder="-67.1601, 18.211\n-67.1588, 18.2101\n-67.1573, 18.2092",
        height=120,
    )
    submitted = st.form_submit_button("Create Road Segment", use_container_width=True)
    if submitted:
        if not name.strip():
            st.error("Name is required.")
        elif not coords_input.strip():
            st.error("Coordinates are required.")
        else:
            try:
                lines = [l.strip() for l in coords_input.strip().splitlines() if l.strip()]
                coordinates = [[float(x) for x in l.replace(",", " ").split()] for l in lines]
                if len(coordinates) < 2:
                    st.error("A LineString requires at least 2 points.")
                else:
                    geom = {"type": "LineString", "coordinates": coordinates}
                    result = APIClient().create_road_segment(
                        name,
                        speed_limit_kph if speed_limit_kph > 0 else None,
                        is_oneway,
                        direction,
                        geom
                    )
                    if result:
                        st.success(f"Road segment '{name}' created with ID {result.get('road_id')}!")
                        st.rerun()
            except ValueError:
                st.error("Invalid coordinates format. Use: lon,lat per line.")

st.divider()

# ── Update / Delete Road Segment ──
st.subheader("Update or Delete Road Segment")

if not items:
    st.info("No road segments loaded. Adjust the bbox filter to load records.")
else:
    options = {f"{s.get('name')} (ID={s.get('road_id')})": s for s in items}
    selected_label = st.selectbox("Select a road segment", list(options.keys()), key="road_select")
    selected = options[selected_label]
    selected_id = selected.get("road_id")

    tab_update, tab_delete = st.tabs(["Update", "Delete"])

    with tab_update:
        with st.form("update_road_form"):
            new_name = st.text_input("Name", value=selected.get("name") or "")
            new_speed = st.number_input("Speed limit (kph)", min_value=0, value=selected.get("speed_limit_kph") or 0)
            update_submitted = st.form_submit_button("Update Road Segment", use_container_width=True)
            if update_submitted:
                payload = {}
                if new_name.strip():
                    payload["name"] = new_name.strip()
                if new_speed >= 0:
                    payload["speed_limit_kph"] = new_speed
                if payload:
                    result = APIClient().update_road_segment_data(selected_id, payload)
                    if result:
                        st.success(f"Road segment ID {selected_id} updated successfully!")
                        st.rerun()
                else:
                    st.error("At least one field must be provided.")

    with tab_delete:
        st.warning(f"You are about to delete '{selected.get('name')}' (ID={selected_id}). This cannot be undone.")
        if st.button("Confirm Delete", use_container_width=True, type="primary"):
            result = APIClient().delete_road_segment(selected_id)
            if result:
                st.success(f"Road segment ID {selected_id} deleted successfully!")
                st.rerun()
