from __future__ import annotations

import os

import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "car_tracking"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "root"),
        port=int(os.getenv("DB_PORT", "5432")),
    )
