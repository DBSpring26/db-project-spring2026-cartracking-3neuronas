from __future__ import annotations

from typing import Optional, Any

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool
from pydantic import BaseModel

from config.dbconfig import PG_DB_CONFIG, POOL_CONFIG


class RoadSegmentCreate(BaseModel):
    name: str
    speed_limit_kph: Optional[int] = None
    is_oneway: Optional[bool] = None
    direction: Optional[str] = None
    geom: dict


class RoadSegmentUpdate(BaseModel):
    name: Optional[str] = None
    speed_limit_kph: Optional[int] = None
    is_oneway: Optional[bool] = None
    direction: Optional[str] = None
    geom: Optional[dict] = None


class RoadSegmentDAO:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            POOL_CONFIG["minconn"],
            POOL_CONFIG["maxconn"],
            **PG_DB_CONFIG,
        )

    def create_road_segment(self, data: RoadSegmentCreate) -> dict:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                INSERT INTO road_segment (name, speed_limit_kph, geom, is_oneway, direction)
                VALUES (
                    %s,
                    %s,
                    ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                    %s,
                    %s
                )
                RETURNING
                    road_id, name, speed_limit_kph,
                    ST_AsGeoJSON(geom)::json AS geom,
                    created_at, is_oneway, direction
                """,
                (
                    data.name,
                    data.speed_limit_kph,
                    psycopg2.extras.Json(data.geom),
                    data.is_oneway,
                    data.direction,
                ),
            )
            row = cursor.fetchone()
            conn.commit()
            return dict(row) if row else None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def get_all_road_segments(
        self,
        limit: int,
        offset: int,
        name: Optional[str],
        min_speed: Optional[int],
        max_speed: Optional[int],
        bbox: Optional[tuple[float, float, float, float]],
    ) -> dict:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            where = []
            params: list[Any] = []

            if name is not None and name != "":
                where.append("name ILIKE %s")
                params.append(f"%{name}%")

            if min_speed is not None:
                where.append("speed_limit_kph >= %s")
                params.append(min_speed)

            if max_speed is not None:
                where.append("speed_limit_kph <= %s")
                params.append(max_speed)

            if bbox is not None:
                where.append(
                    "ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))"
                )
                params.extend(list(bbox))

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""

            cursor.execute(
                f"""
                SELECT road_id, name, speed_limit_kph, created_at, is_oneway, direction
                FROM road_segment
                {where_sql}
                ORDER BY road_id
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            items = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"SELECT COUNT(*) AS count FROM road_segment {where_sql}",
                params,
            )
            count = int(cursor.fetchone()["count"])

            return {"items": items, "limit": limit, "offset": offset, "count": count}
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def get_road_segment_by_id(self, road_id: int) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    road_id, name, speed_limit_kph,
                    ST_AsGeoJSON(geom)::json AS geom,
                    created_at, is_oneway, direction
                FROM road_segment
                WHERE road_id = %s
                """,
                (road_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def update_road_segment(self, road_id: int, data: RoadSegmentUpdate) -> dict | None:
        payload = data.model_dump(exclude_unset=True)
        set_parts: list[str] = []
        params: list[Any] = []

        for field in ["name", "speed_limit_kph", "is_oneway", "direction"]:
            if field in payload:
                set_parts.append(f"{field} = %s")
                params.append(payload[field])

        if "geom" in payload:
            set_parts.append("geom = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)")
            params.append(psycopg2.extras.Json(payload["geom"]))

        if not set_parts:
            return None

        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                f"""
                UPDATE road_segment
                SET {", ".join(set_parts)}
                WHERE road_id = %s
                RETURNING
                    road_id, name, speed_limit_kph,
                    ST_AsGeoJSON(geom)::json AS geom,
                    created_at, is_oneway, direction
                """,
                (*params, road_id),
            )
            row = cursor.fetchone()
            conn.commit()
            return dict(row) if row else None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def delete_road_segment(self, road_id: int) -> bool:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute("DELETE FROM road_segment WHERE road_id = %s", (road_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

