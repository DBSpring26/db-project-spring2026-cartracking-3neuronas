import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool

PG_DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "dpg-d6rbqdkr85hc73a2ovng-a.virginia-postgres.render.com"),
    "database": os.getenv("DB_NAME", "dbproject_y601"),
    "user":     os.getenv("DB_USER", "neurona1"),
    "password": os.getenv("DB_PASSWORD", "YGS3uNZ247ukda0t9RLZ4AGrKYyjPOeq"),
    "port":     int(os.getenv("DB_PORT", "5432")),
}

POOL_CONFIG = {
    "minconn": 1,
    "maxconn": 10,
}