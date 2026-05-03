from fastapi import HTTPException, status
from src.utils import db_manager
from src.security import verify_password, create_access_token  # Убедись, что твои функции лежат тут


class AuthService:
    def __init__(self, db: db_manager):
        self.db = db

    async def login(self, username: str, password: str) -> dict:
        """Бизнес-логика авторизации: поиск, проверка, выдача токена"""

        # 1. Ищем пользователя через наш новый репозиторий
        user = await self.db.users.get_by_username(username)

        # 2. Проверяем пароль
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Выдаем токен
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}