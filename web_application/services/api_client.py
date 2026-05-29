from __future__ import annotations

from typing import Optional, Any

import requests
import streamlit as st

from config import API_BASE_URL


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _handle_response(self, r: requests.Response) -> Optional[dict]:
        try:
            r.raise_for_status()
        except requests.HTTPError:
            try:
                data = r.json()
                msg = data.get("error") or data.get("detail") or str(data)
            except Exception:
                msg = r.text or f"HTTP {r.status_code}"
            st.error(msg)
            return None
        try:
            return r.json()
        except Exception:
            st.error("Invalid JSON response from API")
            return None

    def signup(self, username: str, email: str, password: str) -> Optional[dict]:
        try:
            r = requests.post(
                self._url("/users/signup"),
                json={"username": username, "email": email, "password": password},
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def login(self, username: str, password: str) -> Optional[dict]:
        try:
            r = requests.post(
                self._url("/users/login"),
                json={"username": username, "password": password},
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def get_parking_areas(self, bbox: Optional[str] = None, limit: int = 300) -> Optional[dict]:
        params: dict[str, Any] = {"limit": limit}
        if bbox:
            params["bbox"] = bbox
        try:
            r = requests.get(self._url("/parking-areas/map"), params=params, timeout=15)
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def create_parking_area(self, name: str, capacity, geom: dict) -> Optional[dict]:
        body = {
            "name": name,
            "geom": geom,
        }
        if capacity is not None:
            body["capacity"] = capacity
        try:
            r = requests.post(
                self._url("/parking-areas"),
                json=body,
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def update_parking_area(self, parking_area_id: int, data: dict) -> Optional[dict]:
        try:
            r = requests.put(
                self._url(f"/parking-areas/{parking_area_id}"),
                json=data,
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def delete_parking_area(self, parking_area_id: int) -> Optional[dict]:
        try:
            r = requests.delete(
                self._url(f"/parking-areas/{parking_area_id}"),
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def get_road_segments(self, bbox: Optional[str] = None, limit: int = 5000) -> Optional[dict]:
        params: dict[str, Any] = {"limit": limit}
        if bbox:
            params["bbox"] = bbox
        try:
            r = requests.get(self._url("/road-segments/map"), params=params, timeout=15)
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def create_road_segment(self, name: str, speed_limit_kph, is_oneway: bool, direction: str, geom: dict) -> Optional[dict]:
        body = {
            "name": name,
            "geom": geom,
            "is_oneway": is_oneway,
            "direction": direction,
        }
        if speed_limit_kph is not None:
            body["speed_limit_kph"] = speed_limit_kph
        try:
            r = requests.post(
                self._url("/road-segments"),
                json=body,
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def update_road_segment_data(self, road_id: int, data: dict) -> Optional[dict]:
        try:
            r = requests.put(
                self._url(f"/road-segments/{road_id}"),
                json=data,
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def delete_road_segment(self, road_id: int) -> Optional[dict]:
        try:
            r = requests.delete(
                self._url(f"/road-segments/{road_id}"),
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def get_latest_pings(self, bbox: Optional[str] = None) -> Optional[dict]:
        params: dict[str, Any] = {}
        if bbox:
            params["bbox"] = bbox
        try:
            r = requests.get(self._url("/location-pings/latest"), params=params, timeout=15)
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def create_location_ping(self, vehicle_id: int, ts: str, geom: dict, speed_kph=None, heading_deg=None) -> Optional[dict]:
        body = {
            "vehicle_id": vehicle_id,
            "ts": ts,
            "geom": geom,
        }
        if speed_kph is not None:
            body["speed_kph"] = speed_kph
        if heading_deg is not None:
            body["heading_deg"] = heading_deg
        try:
            r = requests.post(
                self._url("/location-pings"),
                json=body,
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def update_location_ping(self, ping_id: int, data: dict) -> Optional[dict]:
        try:
            r = requests.put(
                self._url(f"/location-pings/{ping_id}"),
                json=data,
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def delete_location_ping(self, ping_id: int) -> Optional[dict]:
        try:
            r = requests.delete(
                self._url(f"/location-pings/{ping_id}"),
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def get_vehicles(self, limit: int = 50) -> Optional[dict]:
        params: dict[str, Any] = {"limit": limit}
        try:
            r = requests.get(self._url("/vehicles"), params=params, timeout=15)
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def get_breadcrumb(self, vehicle_id: int, from_ts: str, to_ts: str) -> Optional[dict]:
        params = {"from_ts": from_ts, "to_ts": to_ts}
        try:
            r = requests.get(
                self._url(f"/vehicles/{vehicle_id}/breadcrumb"),
                params=params,
                timeout=15,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None

    def get_pings_per_day(self, from_ts: Optional[str] = None, to_ts: Optional[str] = None) -> Optional[dict]:
        params: dict[str, Any] = {}
        if from_ts:
            params["from_ts"] = from_ts
        if to_ts:
            params["to_ts"] = to_ts
        try:
            r = requests.get(self._url("/stats/pings-per-day"), params=params, timeout=15)
            return self._handle_response(r)
        except requests.RequestException as e:
            st.error(str(e))
            return None
