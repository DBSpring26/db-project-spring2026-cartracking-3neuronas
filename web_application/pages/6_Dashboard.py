from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from services.api_client import APIClient
from services.auth import require_auth


require_auth()

st.title("Dashboard")

col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From date", value=None)
with col2:
    to_date = st.date_input("To date", value=None)

from_ts = None
to_ts = None
if from_date:
    from_ts = datetime.combine(from_date, datetime.min.time()).isoformat()
if to_date:
    to_ts = datetime.combine(to_date, datetime.max.time()).isoformat()

data = APIClient().get_pings_per_day(from_ts=from_ts, to_ts=to_ts) or {}
items = data.get("items") or []

df = pd.DataFrame(items)
if df.empty:
    st.info("No data to display.")
    st.stop()

fig = px.bar(df, x="day", y="count", title="Location Pings per Day")
st.plotly_chart(fig, width='stretch')
