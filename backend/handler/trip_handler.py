from __future__ import annotations

from datetime import datetime
from typing import Optional

import psycopg2
from fastapi import HTTPException

from dao.trip_dao import TripDAO, TripCreate, TripUpdate


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if value is None or value == "":
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid timestamp format")


def _validate_point(geom: dict, field_name: str):
    if geom.get("type") != "Point":
        raise HTTPException(status_code=400, detail=f"{field_name} is not a valid Point")
    coords = geom.get("coordinates")
    if not isinstance(coords, list) or len(coords) != 2:
        raise HTTPException(status_code=400, detail=f"{field_name} is not a valid Point")


class TripHandler:
    def create_trip(self, data):
        start = _parse_ts(data.start_ts)
        end = _parse_ts(data.end_ts)
        if start is None or end is None:
            raise HTTPException(status_code=400, detail="start_ts and end_ts are required")
        if end <= start:
            raise HTTPException(status_code=400, detail="end_ts must be after start_ts")

        if data.distance_km is not None and data.distance_km < 0:
            raise HTTPException(status_code=400, detail="distance_km must be >= 0")

        start_geom = None
        end_geom = None
        if data.start_geom is not None:
            start_geom = data.start_geom.model_dump()
            _validate_point(start_geom, "start_geom")
        if data.end_geom is not None:
            end_geom = data.end_geom.model_dump()
            _validate_point(end_geom, "end_geom")

        dao = TripDAO()
        try:
            return dao.create_trip(
                TripCreate(
                    vehicle_id=data.vehicle_id,
                    start_ts=data.start_ts,
                    end_ts=data.end_ts,
                    start_geom=start_geom,
                    end_geom=end_geom,
                    distance_km=data.distance_km,
                )
            )
        except psycopg2.errors.ForeignKeyViolation:
            raise HTTPException(status_code=404, detail="vehicle_id does not exist")
        except psycopg2.Error:
            raise HTTPException(status_code=400, detail="invalid geom")

    def get_all_trips(self, limit, offset, vehicle_id, from_ts, to_ts):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="limit and offset must be non-negative")
        f = _parse_ts(from_ts)
        t = _parse_ts(to_ts)
        if f is not None and t is not None and f > t:
            raise HTTPException(status_code=400, detail="invalid time range")

        dao = TripDAO()
        return dao.get_all_trips(limit, offset, vehicle_id, from_ts, to_ts)

    def get_trip_by_id(self, trip_id: int):
        dao = TripDAO()
        result = dao.get_trip_by_id(trip_id)
        if result is None:
            raise HTTPException(status_code=404, detail="trip not found")
        return result

    def update_trip(self, trip_id: int, data):
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(status_code=400, detail="no fields provided for update")

        if "distance_km" in payload and payload["distance_km"] is not None and payload["distance_km"] < 0:
            raise HTTPException(status_code=422, detail="distance_km must be >= 0")

        if "start_ts" in payload and payload["start_ts"] is not None:
            _parse_ts(payload["start_ts"])
        if "end_ts" in payload and payload["end_ts"] is not None:
            _parse_ts(payload["end_ts"])

        if "start_geom" in payload and payload["start_geom"] is not None:
            geom = payload["start_geom"].model_dump() if hasattr(payload["start_geom"], "model_dump") else payload["start_geom"]
            _validate_point(geom, "start_geom")
            payload["start_geom"] = geom

        if "end_geom" in payload and payload["end_geom"] is not None:
            geom = payload["end_geom"].model_dump() if hasattr(payload["end_geom"], "model_dump") else payload["end_geom"]
            _validate_point(geom, "end_geom")
            payload["end_geom"] = geom

        dao = TripDAO()
        existing = dao.get_trip_times(trip_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="trip not found")

        new_start = payload.get("start_ts", existing["start_ts"])
        new_end = payload.get("end_ts", existing["end_ts"])
        start_dt = datetime.fromisoformat(str(new_start))
        end_dt = datetime.fromisoformat(str(new_end))
        if end_dt <= start_dt:
            raise HTTPException(status_code=400, detail="end_ts must be after start_ts")

        try:
            updated = dao.update_trip(trip_id, TripUpdate(**payload))
            if updated is None:
                raise HTTPException(status_code=404, detail="trip not found")
            return updated
        except psycopg2.errors.ForeignKeyViolation:
            raise HTTPException(status_code=404, detail="vehicle_id does not exist")
        except psycopg2.Error:
            raise HTTPException(status_code=400, detail="invalid geom")

    def delete_trip(self, trip_id: int):
        dao = TripDAO()
        deleted = dao.delete_trip(trip_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="trip not found")
        return {"message": "Trip deleted successfully.", "trip_id": trip_id}

