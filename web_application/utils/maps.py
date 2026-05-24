from __future__ import annotations

from typing import Any

import folium
from folium.plugins import Draw


DEFAULT_CENTER = [18.21, -67.14]
DEFAULT_ZOOM = 13


def _map_base() -> folium.Map:
    m = folium.Map(location=DEFAULT_CENTER, zoom_start=DEFAULT_ZOOM, tiles="OpenStreetMap")
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
    m = _map_base()
    for s in segments or []:
        geom = s.get("geom") or {}
        coords = geom.get("coordinates")
        if geom.get("type") != "LineString" or not coords:
            continue
        latlon = [(c[1], c[0]) for c in coords]
        popup = f"name={s.get('name')} speed_limit_kph={s.get('speed_limit_kph')}"
        folium.PolyLine(locations=latlon, popup=popup).add_to(m)
    return m


def build_pings_map(pings: list[dict]) -> folium.Map:
    m = _map_base()
    for p in pings or []:
        geom = p.get("geom") or {}
        coords = geom.get("coordinates")
        if geom.get("type") != "Point" or not coords or len(coords) != 2:
            continue
        lon, lat = coords
        popup = (
            f"vehicle_id={p.get('vehicle_id')} plate_number={p.get('plate_number')} "
            f"ts={p.get('ts')} speed_kph={p.get('speed_kph')}"
        )
        folium.Marker(
            location=(lat, lon),
            popup=popup,
            icon=folium.Icon(icon="car", prefix="fa"),
        ).add_to(m)
    return m


def build_breadcrumb_map(pings: list[dict]) -> folium.Map:
    m = _map_base()
    points: list[tuple[float, float]] = []
    for p in pings or []:
        geom = p.get("geom") or {}
        coords = geom.get("coordinates")
        if geom.get("type") != "Point" or not coords or len(coords) != 2:
            continue
        lon, lat = coords
        points.append((lat, lon))

    if not points:
        return m

    folium.CircleMarker(points[0], radius=7, color="green", fill=True, fill_opacity=1).add_to(m)
    folium.CircleMarker(points[-1], radius=7, color="red", fill=True, fill_opacity=1).add_to(m)
    if len(points) >= 2:
        folium.PolyLine(points, color="blue").add_to(m)
    m.location = list(points[-1])
    return m
