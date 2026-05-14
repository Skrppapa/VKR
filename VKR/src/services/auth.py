from fastapi import HTTPException, status
from src.utils import db_manager
from src.security import verify_password, create_access_token


class AuthService:
    def __init__(self, db: db_manager):
        self.db = db

    async def login(self, username: str, password: str) -> dict:
        """Авторизация: поиск, проверка, выдача токена"""

        # Поиск юзера
        user = await self.db.users.get_by_username(username)

        # Проверка пароля
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                401,
                "Неверный логин или пароль",
                {"WWW-Authenticate": "Bearer"},
            )

        # Выдача токена
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}