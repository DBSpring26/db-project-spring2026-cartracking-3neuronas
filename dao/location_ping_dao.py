from __future__ import annotations

from typing import Optional, Any

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool
from pydantic import BaseModel

from config.dbconfig import PG_DB_CONFIG, POOL_CONFIG


class LocationPingCreate(BaseModel):
    vehicle_id: int
    ts: str
    geom: dict
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None


class LocationPingUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    ts: Optional[str] = None
    geom: Optional[dict] = None
    speed_kph: Optional[float] = None
    heading_deg: Optional[float] = None


class LocationPingDAO:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            POOL_CONFIG["minconn"],
            POOL_CONFIG["maxconn"],
            **PG_DB_CONFIG,
        )

    def create_location_ping(self, data: LocationPingCreate) -> dict:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                INSERT INTO location_ping (vehicle_id, ts, geom, speed_kph, heading_deg)
                VALUES (
                    %s,
                    %s,
                    ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                    %s,
                    %s
                )
                RETURNING
                    ping_id, vehicle_id, ts,
                    ST_AsGeoJSON(geom)::json AS geom,
                    speed_kph, heading_deg
                """,
                (
                    data.vehicle_id,
                    data.ts,
                    psycopg2.extras.Json(data.geom),
                    data.speed_kph,
                    data.heading_deg,
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

    def get_all_location_pings(
        self,
        limit: int,
        offset: int,
        vehicle_id: Optional[int],
        from_ts: Optional[str],
        to_ts: Optional[str],
        bbox: Optional[tuple[float, float, float, float]],
    ) -> dict:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            where = []
            params: list[Any] = []

            if vehicle_id is not None:
                where.append("vehicle_id = %s")
                params.append(vehicle_id)

            if from_ts is not None and from_ts != "":
                where.append("ts >= %s")
                params.append(from_ts)

            if to_ts is not None and to_ts != "":
                where.append("ts <= %s")
                params.append(to_ts)

            if bbox is not None:
                where.append(
                    "ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))"
                )
                params.extend(list(bbox))

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""

            cursor.execute(
                f"""
                SELECT
                    ping_id, vehicle_id, ts,
                    ST_AsGeoJSON(geom)::json AS geom,
                    speed_kph, heading_deg
                FROM location_ping
                {where_sql}
                ORDER BY ts DESC
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            items = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"SELECT COUNT(*) AS count FROM location_ping {where_sql}",
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

    def get_location_ping_by_id(self, ping_id: int) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    ping_id, vehicle_id, ts,
                    ST_AsGeoJSON(geom)::json AS geom,
                    speed_kph, heading_deg
                FROM location_ping
                WHERE ping_id = %s
                """,
                (ping_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def update_location_ping(self, ping_id: int, data: LocationPingUpdate) -> dict | None:
        payload = data.model_dump(exclude_unset=True)
        set_parts: list[str] = []
        params: list[Any] = []

        for field in ["vehicle_id", "ts", "speed_kph", "heading_deg"]:
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
                UPDATE location_ping
                SET {", ".join(set_parts)}
                WHERE ping_id = %s
                RETURNING
                    ping_id, vehicle_id, ts,
                    ST_AsGeoJSON(geom)::json AS geom,
                    speed_kph, heading_deg
                """,
                (*params, ping_id),
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

    def delete_location_ping(self, ping_id: int) -> bool:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute("DELETE FROM location_ping WHERE ping_id = %s", (ping_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

