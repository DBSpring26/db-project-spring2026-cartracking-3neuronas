import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from services.api_client import APIClient
from services.auth import require_auth
from utils.bbox import bbox_from_draw_output, format_bbox
from utils.maps import build_parking_map

require_auth()

st.title("Parking Areas")

if "bbox_parking" not in st.session_state:
    st.session_state["bbox_parking"] = None
if "new_parking_geom" not in st.session_state:
    st.session_state["new_parking_geom"] = None
if "selected_parking_id" not in st.session_state:
    st.session_state["selected_parking_id"] = None

with st.sidebar:
    st.subheader("Bounding box")
    default_min_lon = -67.14
    default_min_lat = 18.20
    default_max_lon = -67.12
    default_max_lat = 18.22
    min_lon = st.number_input("minLon", value=default_min_lon, format="%.6f", key="parking_min_lon")
    min_lat = st.number_input("minLat", value=default_min_lat, format="%.6f", key="parking_min_lat")
    max_lon = st.number_input("maxLon", value=default_max_lon, format="%.6f", key="parking_max_lon")
    max_lat = st.number_input("maxLat", value=default_max_lat, format="%.6f", key="parking_max_lat")
    col_apply, col_reset = st.columns(2)
    with col_apply:
        if st.button("Apply", use_container_width=True):
            st.session_state["bbox_parking"] = format_bbox((min_lon, min_lat, max_lon, max_lat))
    with col_reset:
        if st.button("Reset", use_container_width=True):
            st.session_state["bbox_parking"] = None
            st.session_state["new_parking_geom"] = None
            st.session_state["selected_parking_id"] = None
            for key in ["parking_min_lon", "parking_min_lat", "parking_max_lon", "parking_max_lat"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

bbox = st.session_state.get("bbox_parking")
data = APIClient().get_parking_areas(bbox=bbox) or {}
items = data.get("items") or []

st.caption(f"Showing {len(items)} parking areas.")

m = build_parking_map(items)
draw = st_folium(m, width=None, height=520, returned_objects=["all_drawings"])

if draw and draw.get("all_drawings"):
    for d in draw["all_drawings"]:
        if d.get("geometry", {}).get("type") == "Polygon":
            st.session_state["new_parking_geom"] = d["geometry"]
            break

new_bbox = bbox_from_draw_output(draw or {})
if new_bbox:
    st.session_state["bbox_parking"] = format_bbox(new_bbox)

df = pd.DataFrame(items)
cols = ["parking_area_id", "name", "capacity", "created_at"]
if not df.empty:
    df = df[[c for c in cols if c in df.columns]]
st.dataframe(df, use_container_width=True)

st.divider()

# ── Add New Parking Area ──
st.subheader("Add New Parking Area")
if st.session_state.get("new_parking_geom"):
    st.success("Polygon drawn on map — fill in the details below.")
    geom = st.session_state["new_parking_geom"]
    with st.form("create_parking_form"):
        name = st.text_input("Name", placeholder="e.g. UPRM West Lot")
        capacity = st.number_input("Capacity", min_value=0, value=0)
        submitted = st.form_submit_button("Create Parking Area", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Name is required.")
            else:
                result = APIClient().create_parking_area(name, capacity if capacity > 0 else None, geom)
                if result:
                    st.success(f"Parking area '{name}' created with ID {result.get('parking_area_id')}!")
                    st.session_state["new_parking_geom"] = None
                    st.session_state["bbox_parking"] = None
                    for key in ["parking_min_lon", "parking_min_lat", "parking_max_lon", "parking_max_lat"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
else:
    st.info("Draw a polygon on the map using the polygon tool to create a new parking area.")

st.divider()

# ── Update / Delete Parking Area ──
st.subheader("Update or Delete Parking Area")

if not items:
    st.info("No parking areas loaded. Adjust the bbox filter to load records.")
else:
    options = {f"{a.get('name')} (ID={a.get('parking_area_id')})": a for a in items}
    selected_label = st.selectbox("Select a parking area", list(options.keys()), key="parking_select")
    selected = options[selected_label]
    selected_id = selected.get("parking_area_id")

    tab_update, tab_delete = st.tabs(["Update", "Delete"])

    with tab_update:
        with st.form("update_parking_form"):
            new_name = st.text_input("Name", value=selected.get("name") or "")
            new_capacity = st.number_input("Capacity", min_value=0, value=selected.get("capacity") or 0)
            update_submitted = st.form_submit_button("Update Parking Area", use_container_width=True)
            if update_submitted:
                payload = {}
                if new_name.strip():
                    payload["name"] = new_name.strip()
                if new_capacity >= 0:
                    payload["capacity"] = new_capacity
                if payload:
                    result = APIClient().update_parking_area(selected_id, payload)
                    if result:
                        st.success(f"Parking area ID {selected_id} updated successfully!")
                        st.rerun()
                else:
                    st.error("At least one field must be provided.")

    with tab_delete:
        st.warning(f"You are about to delete '{selected.get('name')}' (ID={selected_id}). This cannot be undone.")
        if st.button("Confirm Delete", use_container_width=True, type="primary"):
            result = APIClient().delete_parking_area(selected_id)
            if result:
                st.success(f"Parking area ID {selected_id} deleted successfully!")
                st.session_state["selected_parking_id"] = None
                st.rerun()
