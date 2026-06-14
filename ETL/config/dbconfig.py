from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set. Copy .env.example to .env and configure it.")
    return value


def get_connection():
    return psycopg2.connect(
        host=_require_env("DB_HOST"),
        database=_require_env("DB_NAME"),
        user=_require_env("DB_USER"),
        password=_require_env("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", "5432")),
    )
