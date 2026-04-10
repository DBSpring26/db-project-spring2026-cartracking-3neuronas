from __future__ import annotations

from typing import Any

import math
import pandas as pd
from psycopg2 import sql
from psycopg2.extras import execute_batch

try:
    from dbconfig import get_connection
except ImportError:  # pragma: no cover
    from config.dbconfig import get_connection


EXPECTED_COLUMNS = {
    "fuel_type": ["fuel_type_id", "name"],
    "vehicle_kind": ["vehicle_kind_id", "name"],
    "vehicle_status": ["vehicle_status_id", "name"],
    "vehicle_type": ["id", "vehicle_kind_id", "fuel_type_id", "emissions_rating", "created_at"],
    "vehicle": [
        "vehicle_id",
        "vehicle_type_id",
        "vehicle_status_id",
        "plate_number",
        "make",
        "model",
        "year",
        "created_at",
    ],
    "trip": ["trip_id", "vehicle_id", "start_ts", "end_ts", "start_geom", "end_geom", "distance_km"],
    "parking_area": ["parking_area_id", "name", "capacity", "geom", "created_at"],
    "road_segment": ["road_id", "name", "speed_limit_kph", "geom", "created_at", "is_oneway", "direction"],
    "location_ping": ["ping_id", "vehicle_id", "ts", "geom", "speed_kph", "heading_deg"],
}

GEOMETRY_COLUMNS = {
    "trip": {"start_geom": "Point", "end_geom": "Point"},
    "parking_area": {"geom": "Polygon"},
    "road_segment": {"geom": "LineString"},
    "location_ping": {"geom": "Point"},
}

LOAD_ORDER = [
    "fuel_type",
    "vehicle_kind",
    "vehicle_status",
    "vehicle_type",
    "vehicle",
    "trip",
    "parking_area",
    "road_segment",
    "location_ping",
]


def create_tables(conn) -> None:
    """Create the project schema exactly as defined by the supplied parquet files."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS fuel_type (
                fuel_type_id INTEGER PRIMARY KEY,
                name TEXT
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_kind (
                vehicle_kind_id INTEGER PRIMARY KEY,
                name TEXT
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_status (
                vehicle_status_id INTEGER PRIMARY KEY,
                name TEXT
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_type (
                id BIGINT PRIMARY KEY,
                vehicle_kind_id INTEGER REFERENCES vehicle_kind(vehicle_kind_id),
                fuel_type_id INTEGER REFERENCES fuel_type(fuel_type_id),
                emissions_rating NUMERIC(10,3),
                created_at TIMESTAMP
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle (
                vehicle_id BIGSERIAL PRIMARY KEY,
                vehicle_type_id BIGINT REFERENCES vehicle_type(id),
                vehicle_status_id INTEGER REFERENCES vehicle_status(vehicle_status_id),
                plate_number TEXT UNIQUE,
                make TEXT,
                model TEXT,
                year INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS trip (
                trip_id BIGSERIAL PRIMARY KEY,
                vehicle_id BIGINT REFERENCES vehicle(vehicle_id),
                start_ts TIMESTAMP,
                end_ts TIMESTAMP,
                start_geom geometry(Point,4326),
                end_geom geometry(Point,4326),
                distance_km NUMERIC(12,3),
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS parking_area (
                parking_area_id BIGSERIAL PRIMARY KEY,
                name TEXT,
                capacity INTEGER,
                geom geometry(Polygon,4326),
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS road_segment (
                road_id BIGSERIAL PRIMARY KEY,
                name TEXT,
                speed_limit_kph INTEGER,
                geom geometry(LineString,4326),
                created_at TIMESTAMP DEFAULT NOW(),
                is_oneway BOOLEAN,
                direction TEXT
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS location_ping (
                ping_id BIGSERIAL PRIMARY KEY,
                vehicle_id BIGINT REFERENCES vehicle(vehicle_id),
                ts TIMESTAMP,
                geom geometry(Point,4326),
                speed_kph NUMERIC(8,3),
                heading_deg NUMERIC(6,2)
            );
            """
        )

    conn.commit()


def truncate_tables(conn) -> None:
    """Clear tables before loading to avoid duplicate rows across runs."""
    with conn.cursor() as cur:
        cur.execute(
            "TRUNCATE TABLE location_ping, road_segment, parking_area, trip, vehicle, "
            "vehicle_type, vehicle_status, vehicle_kind, fuel_type RESTART IDENTITY CASCADE;"
        )
    conn.commit()


def _is_null(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def _normalize_scalar(value: Any) -> Any:
    if _is_null(value):
        return None

    if isinstance(value, memoryview):
        return bytes(value)

    # pandas Timestamp -> native datetime for psycopg2
    if hasattr(value, "to_pydatetime"):
        try:
            return value.to_pydatetime()
        except Exception:
            pass

    # numpy scalars -> native python types
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


def _normalize_wkb_hex(value: Any) -> str | None:
    value = _normalize_scalar(value)
    if value is None:
        return None

    if isinstance(value, bytes):
        return value.hex()

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.startswith("\\x"):
            cleaned = cleaned[2:]
        return cleaned

    raise TypeError(f"Unsupported geometry value type: {type(value)!r}")


def _validate_dataframe(table: str, df: pd.DataFrame) -> None:
    expected = EXPECTED_COLUMNS[table]
    actual = list(df.columns)
    if actual != expected:
        raise ValueError(
            f"Column mismatch in '{table}'. Expected {expected}, but received {actual}."
        )


def load_table(conn, table: str, df: pd.DataFrame, page_size: int = 1000) -> None:
    """Load a dataframe into its destination table, including PostGIS geometries."""
    _validate_dataframe(table, df)

    if df.empty:
        return

    geometry_columns = GEOMETRY_COLUMNS.get(table, {})
    columns = EXPECTED_COLUMNS[table]

    insert_columns = []
    value_sql_parts = []
    for column in columns:
        insert_columns.append(sql.Identifier(column))
        if column in geometry_columns:
            value_sql_parts.append(
                sql.SQL("ST_SetSRID(ST_GeomFromEWKB(decode(%s, 'hex')), 4326)")
            )
        else:
            value_sql_parts.append(sql.SQL("%s"))

    query = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values})").format(
        table=sql.Identifier(table),
        columns=sql.SQL(", ").join(insert_columns),
        values=sql.SQL(", ").join(value_sql_parts),
    )

    records = []
    for row in df.itertuples(index=False, name=None):
        prepared_row = []
        for column, value in zip(columns, row):
            if column in geometry_columns:
                prepared_row.append(_normalize_wkb_hex(value))
            else:
                prepared_row.append(_normalize_scalar(value))
        records.append(tuple(prepared_row))

    with conn.cursor() as cur:
        execute_batch(cur, query.as_string(conn), records, page_size=page_size)
    conn.commit()


def load_all(data: dict[str, pd.DataFrame]) -> None:
    """Create schema and load all parquet-derived dataframes in dependency order."""
    conn = get_connection()
    try:
        create_tables(conn)
        truncate_tables(conn)
        for table in LOAD_ORDER:
            if table not in data:
                raise KeyError(f"Missing dataframe for required table: {table}")
            load_table(conn, table, data[table])
            print(f"Loaded {len(data[table])} rows into {table}.")

        # Synchronize sequences after bulk loading explicit IDs into BIGSERIAL columns
        with conn.cursor() as cur:
            for table, col in [
                ("vehicle", "vehicle_id"),
                ("trip", "trip_id"),
                ("parking_area", "parking_area_id"),
                ("road_segment", "road_id"),
                ("location_ping", "ping_id"),
            ]:
                cur.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), "
                    f"COALESCE((SELECT MAX({col}) FROM {table}), 1));"
                )
        conn.commit()
        print("Sequences synchronized.")
    finally:
        conn.close()
