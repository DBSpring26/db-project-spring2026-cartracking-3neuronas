from __future__ import annotations

from typing import Any, Optional

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool

from ..config.dbconfig import PG_DB_CONFIG, POOL_CONFIG


class StatsDAO:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            POOL_CONFIG["minconn"],
            POOL_CONFIG["maxconn"],
            **PG_DB_CONFIG,
        )

    def get_pings_per_day(self, from_ts: Optional[str], to_ts: Optional[str]) -> dict:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            where = []
            params: list[Any] = []
            if from_ts:
                where.append("ts >= %s")
                params.append(from_ts)
            if to_ts:
                where.append("ts <= %s")
                params.append(to_ts)
            where_sql = ("WHERE " + " AND ".join(where)) if where else ""
            cursor.execute(
                f"""
                SELECT ts::date AS day, COUNT(*) AS count
                FROM location_ping
                {where_sql}
                GROUP BY day
                ORDER BY day ASC
                """,
                params,
            )
            items = [
                {"day": str(r["day"]), "count": int(r["count"])}
                for r in cursor.fetchall()
            ]
            return {"items": items, "count": len(items)}
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)
