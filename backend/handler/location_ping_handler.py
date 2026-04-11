from __future__ import annotations

from datetime import datetime
from typing import Optional

import psycopg2
from fastapi import HTTPException

from dao.location_ping_dao import (
    LocationPingDAO,
    LocationPingCreate,
    LocationPingUpdate,
)


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if value is None or value == "":
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid timestamp format")


def _parse_bbox(bbox: Optional[str]) -> Optional[tuple[float, float, float, float]]:
    if bbox is None or bbox == "":
        return None
    parts = bbox.split(",")
    if len(parts) != 4:
        raise HTTPException(status_code=400, detail="invalid bbox format")
    try:
        min_lon, min_lat, max_lon, max_lat = [float(x) for x in parts]
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid bbox format")
    if min_lon > max_lon or min_lat > max_lat:
        raise HTTPException(status_code=400, detail="invalid bbox values")
    return (min_lon, min_lat, max_lon, max_lat)


def _validate_point(geom: dict):
    if geom.get("type") != "Point":
        raise HTTPException(status_code=400, detail="geom is not a valid Point")
    coords = geom.get("coordinates")
    if not isinstance(coords, list) or len(coords) != 2:
        raise HTTPException(status_code=400, detail="geom is not a valid Point")


class LocationPingHandler:
    def create_location_ping(self, data):
        _parse_ts(data.ts)

        if data.speed_kph is not None and data.speed_kph < 0:
            raise HTTPException(status_code=400, detail="speed_kph must be >= 0")

        if data.heading_deg is not None and not (0 <= data.heading_deg < 360):
            raise HTTPException(status_code=400, detail="heading_deg must be in [0, 360)")

        geom = data.geom.model_dump()
        _validate_point(geom)

        dao = LocationPingDAO()
        try:
            return dao.create_location_ping(
                LocationPingCreate(
                    vehicle_id=data.vehicle_id,
                    ts=data.ts,
                    geom=geom,
                    speed_kph=data.speed_kph,
                    heading_deg=data.heading_deg,
                )
            )
        except psycopg2.errors.ForeignKeyViolation:
            raise HTTPException(status_code=404, detail="vehicle_id does not exist")
        except psycopg2.Error:
            raise HTTPException(status_code=400, detail="invalid geom")

    def get_all_location_pings(self, limit, offset, vehicle_id, from_ts, to_ts, bbox):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="limit and offset must be non-negative")
        f = _parse_ts(from_ts)
        t = _parse_ts(to_ts)
        if f is not None and t is not None and f > t:
            raise HTTPException(status_code=400, detail="invalid time range")

        parsed_bbox = _parse_bbox(bbox)

        dao = LocationPingDAO()
        return dao.get_all_location_pings(limit, offset, vehicle_id, from_ts, to_ts, parsed_bbox)

    def get_location_ping_by_id(self, ping_id: int):
        dao = LocationPingDAO()
        result = dao.get_location_ping_by_id(ping_id)
        if result is None:
            raise HTTPException(status_code=404, detail="location ping not found")
        return result

    def update_location_ping(self, ping_id: int, data):
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(status_code=400, detail="no fields provided for update")

        if "ts" in payload and payload["ts"] is not None:
            _parse_ts(payload["ts"])

        if "speed_kph" in payload and payload["speed_kph"] is not None and payload["speed_kph"] < 0:
            raise HTTPException(status_code=400, detail="speed_kph must be >= 0")

        if "heading_deg" in payload and payload["heading_deg"] is not None:
            if not (0 <= payload["heading_deg"] < 360):
                raise HTTPException(status_code=400, detail="heading_deg must be in [0, 360)")

        if "geom" in payload and payload["geom"] is not None:
            geom = payload["geom"].model_dump() if hasattr(payload["geom"], "model_dump") else payload["geom"]
            _validate_point(geom)
            payload["geom"] = geom

        dao = LocationPingDAO()
        try:
            updated = dao.update_location_ping(ping_id, LocationPingUpdate(**payload))
            if updated is None:
                raise HTTPException(status_code=404, detail="location ping not found")
            return updated
        except psycopg2.errors.ForeignKeyViolation:
            raise HTTPException(status_code=404, detail="vehicle_id does not exist")
        except psycopg2.Error:
            raise HTTPException(status_code=400, detail="invalid geom")

    def delete_location_ping(self, ping_id: int):
        dao = LocationPingDAO()
        deleted = dao.delete_location_ping(ping_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="location ping not found")
        return {"message": "Location ping deleted successfully.", "ping_id": ping_id}

