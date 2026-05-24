from __future__ import annotations

from typing import Optional

import psycopg2
from fastapi import HTTPException

from ..dao.road_segment_dao import RoadSegmentDAO, RoadSegmentCreate, RoadSegmentUpdate


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


def _validate_linestring(geom: dict):
    if geom.get("type") != "LineString":
        raise HTTPException(status_code=400, detail="geom is not a valid LineString")
    coords = geom.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        raise HTTPException(status_code=400, detail="geom is not a valid LineString")


class RoadSegmentHandler:
    def create_road_segment(self, data):
        if data.name is None or data.name.strip() == "":
            raise HTTPException(status_code=400, detail="name is required")

        if data.speed_limit_kph is not None and data.speed_limit_kph < 0:
            raise HTTPException(status_code=400, detail="speed_limit_kph must be >= 0")

        if data.direction is not None and data.direction not in ("both", "forward"):
            raise HTTPException(status_code=400, detail='direction must be "both" or "forward"')

        geom = data.geom.model_dump()
        _validate_linestring(geom)

        dao = RoadSegmentDAO()
        try:
            return dao.create_road_segment(
                RoadSegmentCreate(
                    name=data.name.strip(),
                    speed_limit_kph=data.speed_limit_kph,
                    is_oneway=data.is_oneway,
                    direction=data.direction,
                    geom=geom,
                )
            )
        except psycopg2.Error:
            raise HTTPException(status_code=400, detail="invalid geom")

    def get_all_road_segments(self, limit, offset, name, min_speed, max_speed, bbox):
        if limit < 0 or offset < 0:
            raise HTTPException(status_code=400, detail="limit and offset must be non-negative")
        if min_speed is not None and min_speed < 0:
            raise HTTPException(status_code=400, detail="min_speed must be >= 0")
        if max_speed is not None and max_speed < 0:
            raise HTTPException(status_code=400, detail="max_speed must be >= 0")
        if min_speed is not None and max_speed is not None and min_speed > max_speed:
            raise HTTPException(status_code=400, detail="invalid speed range")

        parsed_bbox = _parse_bbox(bbox)

        dao = RoadSegmentDAO()
        return dao.get_all_road_segments(limit, offset, name, min_speed, max_speed, parsed_bbox)

    def get_road_segment_by_id(self, road_id: int):
        dao = RoadSegmentDAO()
        result = dao.get_road_segment_by_id(road_id)
        if result is None:
            raise HTTPException(status_code=404, detail="road segment not found")
        return result

    def update_road_segment(self, road_id: int, data):
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(status_code=400, detail="no fields provided for update")

        if "name" in payload and payload["name"] is not None and payload["name"].strip() == "":
            raise HTTPException(status_code=400, detail="name must be non-empty")

        if "speed_limit_kph" in payload and payload["speed_limit_kph"] is not None:
            if payload["speed_limit_kph"] < 0:
                raise HTTPException(status_code=400, detail="speed_limit_kph must be >= 0")

        if "direction" in payload and payload["direction"] is not None:
            if payload["direction"] not in ("both", "forward"):
                raise HTTPException(status_code=400, detail='direction must be "both" or "forward"')

        if "geom" in payload and payload["geom"] is not None:
            geom = payload["geom"].model_dump() if hasattr(payload["geom"], "model_dump") else payload["geom"]
            _validate_linestring(geom)
            payload["geom"] = geom

        if "name" in payload and payload["name"] is not None:
            payload["name"] = payload["name"].strip()

        dao = RoadSegmentDAO()
        try:
            updated = dao.update_road_segment(road_id, RoadSegmentUpdate(**payload))
            if updated is None:
                raise HTTPException(status_code=404, detail="road segment not found")
            return updated
        except psycopg2.Error:
            raise HTTPException(status_code=400, detail="invalid geom")

    def delete_road_segment(self, road_id: int):
        dao = RoadSegmentDAO()
        deleted = dao.delete_road_segment(road_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="road segment not found")
        return {"message": "Road segment deleted successfully.", "road_id": road_id}

    def get_road_segments_map(self, limit, offset, name, min_speed, max_speed, bbox_str):
        parsed_bbox = None
        if bbox_str:
            try:
                parts = [float(x) for x in bbox_str.split(",")]
                if len(parts) != 4:
                    raise ValueError
                parsed_bbox = tuple(parts)
            except ValueError:
                raise HTTPException(status_code=400, detail="invalid bbox format")
        dao = RoadSegmentDAO()
        return dao.get_road_segments_map(limit, offset, name, min_speed, max_speed, parsed_bbox)

