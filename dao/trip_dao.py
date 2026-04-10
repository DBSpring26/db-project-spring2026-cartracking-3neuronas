from __future__ import annotations

from typing import Optional, Any

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool
from pydantic import BaseModel

from config.dbconfig import PG_DB_CONFIG, POOL_CONFIG


class TripCreate(BaseModel):
    vehicle_id: int
    start_ts: str
    end_ts: str
    start_geom: Optional[dict] = None
    end_geom: Optional[dict] = None
    distance_km: Optional[float] = None


class TripUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    start_geom: Optional[dict] = None
    end_geom: Optional[dict] = None
    distance_km: Optional[float] = None


class TripDAO:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            POOL_CONFIG["minconn"],
            POOL_CONFIG["maxconn"],
            **PG_DB_CONFIG,
        )

    def create_trip(self, data: TripCreate) -> dict:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                INSERT INTO trip (vehicle_id, start_ts, end_ts, start_geom, end_geom, distance_km)
                VALUES (
                    %s,
                    %s,
                    %s,
                    CASE WHEN %s IS NULL THEN NULL ELSE ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) END,
                    CASE WHEN %s IS NULL THEN NULL ELSE ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) END,
                    %s
                )
                RETURNING
                    trip_id, vehicle_id, start_ts, end_ts,
                    CASE WHEN start_geom IS NULL THEN NULL ELSE ST_AsGeoJSON(start_geom)::json END AS start_geom,
                    CASE WHEN end_geom IS NULL THEN NULL ELSE ST_AsGeoJSON(end_geom)::json END AS end_geom,
                    distance_km
                """,
                (
                    data.vehicle_id,
                    data.start_ts,
                    data.end_ts,
                    None if data.start_geom is None else 1,
                    None if data.start_geom is None else psycopg2.extras.Json(data.start_geom),
                    None if data.end_geom is None else 1,
                    None if data.end_geom is None else psycopg2.extras.Json(data.end_geom),
                    data.distance_km,
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

    def get_all_trips(
        self,
        limit: int,
        offset: int,
        vehicle_id: Optional[int],
        from_ts: Optional[str],
        to_ts: Optional[str],
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
                where.append("start_ts >= %s")
                params.append(from_ts)

            if to_ts is not None and to_ts != "":
                where.append("start_ts <= %s")
                params.append(to_ts)

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""

            cursor.execute(
                f"""
                SELECT trip_id, vehicle_id, start_ts, end_ts, distance_km
                FROM trip
                {where_sql}
                ORDER BY start_ts DESC
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            items = [dict(r) for r in cursor.fetchall()]

            cursor.execute(f"SELECT COUNT(*) AS count FROM trip {where_sql}", params)
            count = int(cursor.fetchone()["count"])

            return {"items": items, "limit": limit, "offset": offset, "count": count}
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def get_trip_by_id(self, trip_id: int) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    trip_id, vehicle_id, start_ts, end_ts,
                    CASE WHEN start_geom IS NULL THEN NULL ELSE ST_AsGeoJSON(start_geom)::json END AS start_geom,
                    CASE WHEN end_geom IS NULL THEN NULL ELSE ST_AsGeoJSON(end_geom)::json END AS end_geom,
                    distance_km
                FROM trip
                WHERE trip_id = %s
                """,
                (trip_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def get_trip_times(self, trip_id: int) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                "SELECT start_ts, end_ts FROM trip WHERE trip_id = %s",
                (trip_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def update_trip(self, trip_id: int, data: TripUpdate) -> dict | None:
        payload = data.model_dump(exclude_unset=True)
        set_parts: list[str] = []
        params: list[Any] = []

        for field in ["vehicle_id", "start_ts", "end_ts", "distance_km"]:
            if field in payload:
                set_parts.append(f"{field} = %s")
                params.append(payload[field])

        if "start_geom" in payload:
            set_parts.append(
                "start_geom = CASE WHEN %s IS NULL THEN NULL ELSE ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) END"
            )
            if payload["start_geom"] is None:
                params.extend([None, None])
            else:
                params.extend([1, psycopg2.extras.Json(payload["start_geom"])])

        if "end_geom" in payload:
            set_parts.append(
                "end_geom = CASE WHEN %s IS NULL THEN NULL ELSE ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) END"
            )
            if payload["end_geom"] is None:
                params.extend([None, None])
            else:
                params.extend([1, psycopg2.extras.Json(payload["end_geom"])])

        if not set_parts:
            return None

        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                f"""
                UPDATE trip
                SET {", ".join(set_parts)}
                WHERE trip_id = %s
                RETURNING
                    trip_id, vehicle_id, start_ts, end_ts,
                    CASE WHEN start_geom IS NULL THEN NULL ELSE ST_AsGeoJSON(start_geom)::json END AS start_geom,
                    CASE WHEN end_geom IS NULL THEN NULL ELSE ST_AsGeoJSON(end_geom)::json END AS end_geom,
                    distance_km
                """,
                (*params, trip_id),
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

    def delete_trip(self, trip_id: int) -> bool:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute("DELETE FROM trip WHERE trip_id = %s", (trip_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

