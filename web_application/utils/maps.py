from __future__ import annotations

from typing import Any

import folium
from folium.plugins import Draw


DEFAULT_CENTER = [18.21, -67.14]
DEFAULT_ZOOM = 13


def _map_base(draw: bool = True) -> folium.Map:
    m = folium.Map(location=DEFAULT_CENTER, zoom_start=DEFAULT_ZOOM, tiles="OpenStreetMap")
    if draw:
        Draw(export=False).add_to(m)
    return m


def build_parking_map(parking_areas: list[dict]) -> folium.Map:
    m = _map_base()

    css = """
<style>
path.leaflet-interactive:focus {
    outline: none !important;
    box-shadow: none !important;
}
</style>
"""
    m.get_root().html.add_child(folium.Element(css))

    for a in parking_areas or []:
        geom = a.get("geom") or {}
        coords = geom.get("coordinates")
        if geom.get("type") != "Polygon" or not coords:
            continue
        ring = coords[0]
        locations = [[c[1], c[0]] for c in ring]
        folium.Polygon(
            locations=locations,
            color="#3388ff",
            weight=2,
            fill=True,
            fill_color="#3388ff",
            fill_opacity=0.4,
            smooth_factor=1.0,
            popup=folium.Popup(
                f"<b>ID:</b> {a.get('parking_area_id')}<br><b>Capacity:</b> {a.get('capacity')}",
                max_width=200
            ),
        ).add_to(m)
    Draw(export=False).add_to(m)

    folium.MacroElement().add_to(m)
    return m


def build_roads_map(segments: list[dict]) -> folium.Map:
    m = _map_base(draw=False)

    css = """
<style>
path.leaflet-interactive:focus {
    outline: none !important;
    box-shadow: none !important;
}
</style>
"""
    m.get_root().html.add_child(folium.Element(css))

    def get_color(speed):
        if speed is None:
            return "#888888"
        elif speed <= 30:
            return "#00cc00"
        elif speed <= 60:
            return "#ff9900"
        else:
            return "#ff0000"

    for s in segments or []:
        geom = s.get("geom") or {}
        coords = geom.get("coordinates")
        if geom.get("type") != "LineString" or not coords:
            continue
        latlon = [(c[1], c[0]) for c in coords]
        speed = s.get("speed_limit_kph")
        color = get_color(speed)
        popup = f"<b>{s.get('name')}</b><br>Speed limit: {speed} kph"
        folium.PolyLine(
            locations=latlon,
            color=color,
            weight=3,
            opacity=0.8,
            popup=folium.Popup(popup, max_width=200),
        ).add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 30px; right: 30px; z-index: 1000;
                background: white; padding: 10px; border-radius: 8px;
                border: 2px solid #333; font-size: 12px; color: #333;">
        <b style="color:#333;">Speed limit</b><br>
        <span style="color:#00cc00; font-size:16px;">●</span>
        <span style="color:#333;">≤ 30 kph</span><br>
        <span style="color:#ff9900; font-size:16px;">●</span>
        <span style="color:#333;">31–60 kph</span><br>
        <span style="color:#ff0000; font-size:16px;">●</span>
        <span style="color:#333;">> 60 kph</span><br>
        <span style="color:#888888; font-size:16px;">●</span>
        <span style="color:#333;">Unknown</span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def build_pings_map(pings: list[dict]) -> folium.Map:
    m = _map_base()
    for p in pings or []:
        geom = p.get("geom") or {}
        coords = geom.get("coordinates")
        if geom.get("type") != "Point" or not coords or len(coords) != 2:
            continue
        lon, lat = coords
        popup_html = (
            f"<b>Vehicle ID:</b> {p.get('vehicle_id')}<br>"
            f"<b>Plate:</b> {p.get('plate_number')}<br>"
            f"<b>Timestamp:</b> {p.get('ts')}<br>"
            f"<b>Speed:</b> {p.get('speed_kph')} kph<br>"
            f"<b>Heading:</b> {p.get('heading_deg')} deg"
        )
        folium.Marker(
            location=(lat, lon),
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{p.get('plate_number')}",
            icon=folium.Icon(icon="car", prefix="fa"),
        ).add_to(m)
    return m


def build_breadcrumb_map(pings: list[dict]) -> folium.Map:
    m = _map_base()

    # 1. Group pings by trip_id
    trips = {}
    for p in pings or []:
        geom = p.get("geom") or {}
        coords = geom.get("coordinates")
        if geom.get("type") != "Point" or not coords or len(coords) != 2:
            continue

        trip_id = p.get("trip_id")
        lon, lat = coords

        if trip_id not in trips:
            trips[trip_id] = []
        trips[trip_id].append((lat, lon))

    # 2. Draw each trip separately
    for trip_id, points in trips.items():
        if not points:
            continue

        # Draw the line for this specific trip
        if len(points) >= 2:
            folium.PolyLine(points, color="blue", weight=2.5).add_to(m)

        # Optional: Mark the start and end of this specific trip
        folium.CircleMarker(points[0], radius=5, color="green", fill=True).add_to(m)
        folium.CircleMarker(points[-1], radius=5, color="red", fill=True).add_to(m)

    return m
