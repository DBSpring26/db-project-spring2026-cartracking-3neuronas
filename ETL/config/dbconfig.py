from __future__ import annotations

import os

import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "dpg-d6rbqdkr85hc73a2ovng-a.virginia-postgres.render.com"),
        database=os.getenv("DB_NAME", "dbproject_y601"),
        user=os.getenv("DB_USER", "neurona1"),
        password=os.getenv("DB_PASSWORD", "YGS3uNZ247ukda0t9RLZ4AGrKYyjPOeq"),
        port=int(os.getenv("DB_PORT", "5432")),
    )
