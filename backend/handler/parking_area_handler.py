from __future__ import annotations

from typing import Optional

import psycopg2
from fastapi import HTTPException

from ..dao.parking_area_dao import ParkingAreaDAO, ParkingAreaCreate, ParkingAreaUpdate


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


def _validate_polygon(geom: dict):
    if geom.get("type") != "Polygon":
        raise HTTPException(status_code=400, detail="geom is not a valid Polygon")
    coords = geom.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 1:
        raise HTTPException(status_code=400, detail="geom is not a valid Polygon")
    ring = coords[0]
    if not isinstance(ring, list) or len(ring) < 4:
        raise HTTPException(status_code=400, detail="geom is not a valid Polygon")
    if ring[0] != ring[-1]:
        raise HTTPException(status_code=400, detail="Polygon must be closed")


class ParkingAreaHandler:
    def create_parking_area(self, data):
        if data.name is None or data.name.strip() == "":
            raise HTTPException(status_code=400, detail="name is required")
        if data.capacity is not None and data.capacity < 0:
            raise HTTPException(status_code=400, detail="capacity must be >= 0")

        geom = data.geom.model_dump()
        _validate_polygon(geom)

        dao = ParkingAreaDAO()
        try:
            return dao.create_parking_area(
                ParkingAreaCreate(
                    name=data.name.strip(),
                    capacity=data.capacity,
                    geom=geom,
                )
            )
        except psycopg2.Error:
            raise HTTPException(status_code=400, detail="invalid geom")

    def get_all_parking_areas(self, limit, offset, name, bbox):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="limit and offset must be non-negative")
        parsed_bbox = _parse_bbox(bbox)
        dao = ParkingAreaDAO()
        return dao.get_all_parking_areas(limit, offset, name, parsed_bbox)

    def get_parking_area_by_id(self, parking_area_id: int):
        dao = ParkingAreaDAO()
        result = dao.get_parking_area_by_id(parking_area_id)
        if result is None:
            raise HTTPException(status_code=404, detail="parking area not found")
        return result

    def update_parking_area(self, parking_area_id: int, data):
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(status_code=400, detail="no fields provided for update")

        if "name" in payload and payload["name"] is not None and payload["name"].strip() == "":
            raise HTTPException(status_code=400, detail="name must be non-empty")

        if "capacity" in payload and payload["capacity"] is not None and payload["capacity"] < 0:
            raise HTTPException(status_code=400, detail="capacity must be >= 0")

        if "geom" in payload and payload["geom"] is not None:
            geom = payload["geom"].model_dump() if hasattr(payload["geom"], "model_dump") else payload["geom"]
            _validate_polygon(geom)
            payload["geom"] = geom

        if "name" in payload and payload["name"] is not None:
            payload["name"] = payload["name"].strip()

        dao = ParkingAreaDAO()
        try:
            updated = dao.update_parking_area(parking_area_id, ParkingAreaUpdate(**payload))
            if updated is None:
                raise HTTPException(status_code=404, detail="parking area not found")
            return updated
        except psycopg2.Error:
            raise HTTPException(status_code=400, detail="invalid geom")

    def delete_parking_area(self, parking_area_id: int):
        dao = ParkingAreaDAO()
        deleted = dao.delete_parking_area(parking_area_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="parking area not found")
        return {"message": "Parking area deleted successfully.", "parking_area_id": parking_area_id}

    def get_parking_areas_map(self, limit, offset, name, bbox_str):
        parsed_bbox = None
        if bbox_str:
            try:
                parts = [float(x) for x in bbox_str.split(",")]
                if len(parts) != 4:
                    raise ValueError
                parsed_bbox = tuple(parts)
            except ValueError:
                raise HTTPException(status_code=400, detail="invalid bbox format")
        dao = ParkingAreaDAO()
        return dao.get_parking_areas_map(limit, offset, name, parsed_bbox)

