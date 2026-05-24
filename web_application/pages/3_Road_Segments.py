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
    min_lon = st.number_input("minLon", value=-67.14, format="%.6f")
    min_lat = st.number_input("minLat", value=18.20, format="%.6f")
    max_lon = st.number_input("maxLon", value=-67.12, format="%.6f")
    max_lat = st.number_input("maxLat", value=18.22, format="%.6f")
    if st.button("Apply"):
        st.session_state["bbox_roads"] = format_bbox((min_lon, min_lat, max_lon, max_lat))

bbox = st.session_state.get("bbox_roads")
data = APIClient().get_road_segments(bbox=bbox) or {}
items = data.get("items") or []

m = build_roads_map(items)
draw = st_folium(m, width=None, height=520)
new_bbox = bbox_from_draw_output(draw or {})
if new_bbox:
    st.session_state["bbox_roads"] = format_bbox(new_bbox)

df = pd.DataFrame(items)
cols = ["road_id", "name", "speed_limit_kph", "created_at"]
if not df.empty:
    df = df[[c for c in cols if c in df.columns]]
st.dataframe(df, use_container_width=True)
