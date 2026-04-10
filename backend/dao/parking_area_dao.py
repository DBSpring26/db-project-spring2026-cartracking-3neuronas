from __future__ import annotations

from typing import Optional, Any

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool
from pydantic import BaseModel

from config.dbconfig import PG_DB_CONFIG, POOL_CONFIG


class ParkingAreaCreate(BaseModel):
    name: str
    capacity: Optional[int] = None
    geom: dict


class ParkingAreaUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    geom: Optional[dict] = None


class ParkingAreaDAO:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            POOL_CONFIG["minconn"],
            POOL_CONFIG["maxconn"],
            **PG_DB_CONFIG,
        )

    def create_parking_area(self, data: ParkingAreaCreate) -> dict:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                INSERT INTO parking_area (name, capacity, geom)
                VALUES (
                    %s,
                    %s,
                    ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
                )
                RETURNING
                    parking_area_id, name, capacity,
                    ST_AsGeoJSON(geom)::json AS geom,
                    created_at
                """,
                (data.name, data.capacity, psycopg2.extras.Json(data.geom)),
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

    def get_all_parking_areas(
        self,
        limit: int,
        offset: int,
        name: Optional[str],
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

            if bbox is not None:
                where.append(
                    "ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))"
                )
                params.extend(list(bbox))

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""

            cursor.execute(
                f"""
                SELECT parking_area_id, name, capacity, created_at
                FROM parking_area
                {where_sql}
                ORDER BY parking_area_id
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            items = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"SELECT COUNT(*) AS count FROM parking_area {where_sql}",
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

    def get_parking_area_by_id(self, parking_area_id: int) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    parking_area_id, name, capacity,
                    ST_AsGeoJSON(geom)::json AS geom,
                    created_at
                FROM parking_area
                WHERE parking_area_id = %s
                """,
                (parking_area_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def update_parking_area(self, parking_area_id: int, data: ParkingAreaUpdate) -> dict | None:
        payload = data.model_dump(exclude_unset=True)
        set_parts: list[str] = []
        params: list[Any] = []

        for field in ["name", "capacity"]:
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
                UPDATE parking_area
                SET {", ".join(set_parts)}
                WHERE parking_area_id = %s
                RETURNING
                    parking_area_id, name, capacity,
                    ST_AsGeoJSON(geom)::json AS geom,
                    created_at
                """,
                (*params, parking_area_id),
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

    def delete_parking_area(self, parking_area_id: int) -> bool:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                "DELETE FROM parking_area WHERE parking_area_id = %s",
                (parking_area_id,),
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

