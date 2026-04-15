from __future__ import annotations

from typing import Optional, Any

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool
from pydantic import BaseModel

from ..config.dbconfig import PG_DB_CONFIG, POOL_CONFIG


class VehicleCreate(BaseModel):
    vehicle_type_id: int
    vehicle_status_id: int
    plate_number: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: int


class VehicleUpdate(BaseModel):
    vehicle_type_id: Optional[int] = None
    vehicle_status_id: Optional[int] = None
    plate_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed != "" else None


class VehicleDAO:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            POOL_CONFIG["minconn"],
            POOL_CONFIG["maxconn"],
            **PG_DB_CONFIG,
        )

    def create_vehicle(self, data: VehicleCreate) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            result = None
            cursor.execute(
                """
                INSERT INTO vehicle (vehicle_type_id, vehicle_status_id, plate_number, make, model, year)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING vehicle_id, vehicle_type_id, vehicle_status_id, plate_number, make, model, year, created_at
                """,
                (
                    data.vehicle_type_id,
                    data.vehicle_status_id,
                    data.plate_number,
                    _normalize_text(data.make),
                    _normalize_text(data.model),
                    data.year,
                ),
            )
            row = cursor.fetchone()
            result = dict(row) if row else None
            conn.commit()
            return result
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def get_all_vehicles(
        self,
        limit: int,
        offset: int,
        status: Optional[str],
        plate_number: Optional[str],
    ) -> dict:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            where = []
            params: list[Any] = []

            if status is not None and status != "":
                if status.isdigit():
                    where.append("v.vehicle_status_id = %s")
                    params.append(int(status))
                else:
                    where.append("LOWER(vs.name) = LOWER(%s)")
                    params.append(status)

            if plate_number is not None and plate_number != "":
                where.append("v.plate_number ILIKE %s")
                params.append(f"%{plate_number}%")

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""

            cursor.execute(
                f"""
                SELECT
                    v.vehicle_id, v.plate_number, v.make, v.model, v.year,
                    v.vehicle_type_id, v.vehicle_status_id, v.created_at
                FROM vehicle v
                JOIN vehicle_status vs ON vs.vehicle_status_id = v.vehicle_status_id
                {where_sql}
                ORDER BY v.vehicle_id
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            items = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM vehicle v
                JOIN vehicle_status vs ON vs.vehicle_status_id = v.vehicle_status_id
                {where_sql}
                """,
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

    def get_vehicle_by_id(self, vehicle_id: int) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    v.vehicle_id, v.vehicle_type_id, v.vehicle_status_id,
                    v.plate_number, v.make, v.model, v.year, v.created_at,
                    vs.name AS status
                FROM vehicle v
                JOIN vehicle_status vs ON vs.vehicle_status_id = v.vehicle_status_id
                WHERE v.vehicle_id = %s
                """,
                (vehicle_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def update_vehicle(self, vehicle_id: int, data: VehicleUpdate) -> dict | None:
        payload = data.model_dump(exclude_unset=True)
        if "make" in payload:
            payload["make"] = _normalize_text(payload["make"])
        if "model" in payload:
            payload["model"] = _normalize_text(payload["model"])

        set_parts: list[str] = []
        params: list[Any] = []
        for field in [
            "vehicle_type_id",
            "vehicle_status_id",
            "plate_number",
            "make",
            "model",
            "year",
        ]:
            if field in payload:
                set_parts.append(f"{field} = %s")
                params.append(payload[field])

        if not set_parts:
            return None

        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                f"""
                UPDATE vehicle
                SET {", ".join(set_parts)}
                WHERE vehicle_id = %s
                RETURNING vehicle_id, vehicle_type_id, vehicle_status_id, plate_number, make, model, year, created_at
                """,
                (*params, vehicle_id),
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

    def delete_vehicle(self, vehicle_id: int) -> bool:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute("DELETE FROM vehicle WHERE vehicle_id = %s", (vehicle_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def vehicle_exists(self, vehicle_id: int) -> bool:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute("SELECT 1 FROM vehicle WHERE vehicle_id = %s", (vehicle_id,))
            return cursor.fetchone() is not None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def get_vehicle_current_location(self, vehicle_id: int) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    v.vehicle_id,
                    v.plate_number,
                    vs.name AS status,
                    vk.name AS vehicle_kind,
                    ft.name AS fuel_type,
                    vt.emissions_rating
                FROM vehicle v
                JOIN vehicle_status vs ON vs.vehicle_status_id = v.vehicle_status_id
                JOIN vehicle_type vt ON vt.id = v.vehicle_type_id
                JOIN vehicle_kind vk ON vk.vehicle_kind_id = vt.vehicle_kind_id
                JOIN fuel_type ft ON ft.fuel_type_id = vt.fuel_type_id
                WHERE v.vehicle_id = %s
                """,
                (vehicle_id,),
            )
            base = cursor.fetchone()
            if base is None:
                return None

            cursor.execute(
                """
                SELECT
                    lp.ts AS last_ts,
                    ST_AsGeoJSON(lp.geom)::json AS last_geom,
                    lp.speed_kph,
                    lp.heading_deg
                FROM location_ping lp
                WHERE lp.vehicle_id = %s
                ORDER BY lp.ts DESC
                LIMIT 1
                """,
                (vehicle_id,),
            )
            ping = cursor.fetchone()
            if ping is None:
                return {}

            result = dict(base)
            result.update(dict(ping))
            return result
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def get_vehicle_pings(
        self,
        vehicle_id: int,
        limit: int,
        offset: int,
        from_ts: Optional[str],
        to_ts: Optional[str],
    ) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute("SELECT 1 FROM vehicle WHERE vehicle_id = %s", (vehicle_id,))
            if cursor.fetchone() is None:
                return None

            where = ["vehicle_id = %s"]
            params: list[Any] = [vehicle_id]

            if from_ts is not None and from_ts != "":
                where.append("ts >= %s")
                params.append(from_ts)
            if to_ts is not None and to_ts != "":
                where.append("ts <= %s")
                params.append(to_ts)

            where_sql = "WHERE " + " AND ".join(where)

            cursor.execute(
                f"""
                SELECT
                    ping_id, ts,
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

            return {
                "vehicle_id": vehicle_id,
                "items": items,
                "limit": limit,
                "offset": offset,
                "count": count,
            }
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

    def get_vehicle_trips(
        self,
        vehicle_id: int,
        limit: int,
        offset: int,
        from_ts: Optional[str],
        to_ts: Optional[str],
    ) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute("SELECT 1 FROM vehicle WHERE vehicle_id = %s", (vehicle_id,))
            if cursor.fetchone() is None:
                return None

            where = ["vehicle_id = %s"]
            params: list[Any] = [vehicle_id]

            if from_ts is not None and from_ts != "":
                where.append("start_ts >= %s")
                params.append(from_ts)
            if to_ts is not None and to_ts != "":
                where.append("start_ts <= %s")
                params.append(to_ts)

            where_sql = "WHERE " + " AND ".join(where)

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

            return {
                "vehicle_id": vehicle_id,
                "items": items,
                "limit": limit,
                "offset": offset,
                "count": count,
            }
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)

