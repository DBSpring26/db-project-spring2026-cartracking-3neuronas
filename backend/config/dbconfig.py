import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool

PG_DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "car_tracking"),
    "user":     os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "port":     int(os.getenv("DB_PORT", "5432")),
}

POOL_CONFIG = {
    "minconn": 1,
    "maxconn": 10,
}