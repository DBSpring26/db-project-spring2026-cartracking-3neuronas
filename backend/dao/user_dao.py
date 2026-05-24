from __future__ import annotations

import bcrypt
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool
from pydantic import BaseModel

from ..config.dbconfig import PG_DB_CONFIG, POOL_CONFIG


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserDAO:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            POOL_CONFIG["minconn"],
            POOL_CONFIG["maxconn"],
            **PG_DB_CONFIG,
        )

    def create_user(self, data: UserCreate) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            password_hash = bcrypt.hashpw(
                data.password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            cursor.execute(
                """
                INSERT INTO app_user (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING user_id, username, email, created_at
                """,
                (data.username.strip(), data.email.strip(), password_hash),
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

    def get_user_by_username(self, username: str) -> dict | None:
        conn = self.pool.getconn()
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            cursor.execute(
                "SELECT user_id, username, email, password_hash FROM app_user WHERE username = %s",
                (username,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.pool.putconn(conn)
