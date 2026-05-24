import bcrypt
from fastapi import HTTPException

from ..dao.user_dao import UserDAO, UserCreate, UserLogin


class UserHandler:
    def signup(self, data: UserCreate) -> dict:
        if not data.username.strip():
            raise HTTPException(status_code=400, detail="username is required")
        if not data.email.strip():
            raise HTTPException(status_code=400, detail="email is required")
        if not data.password:
            raise HTTPException(status_code=400, detail="password is required")
        dao = UserDAO()
        try:
            result = dao.create_user(data)
        except Exception as e:
            if "unique" in str(e).lower():
                raise HTTPException(
                    status_code=409, detail="username or email already exists"
                )
            raise HTTPException(status_code=500, detail="internal server error")
        if result is None:
            raise HTTPException(status_code=500, detail="could not create user")
        return result

    def login(self, data: UserLogin) -> dict:
        dao = UserDAO()
        user = dao.get_user_by_username(data.username)
        if user is None:
            raise HTTPException(status_code=401, detail="invalid username or password")
        match = bcrypt.checkpw(
            data.password.encode("utf-8"),
            user["password_hash"].encode("utf-8"),
        )
        if not match:
            raise HTTPException(status_code=401, detail="invalid username or password")
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
        }
