from fastapi import HTTPException, status
from src.utils import db_manager
from src.security import verify_password, create_access_token
from src.utils.logger import log


class AuthService:
    def __init__(self, db: db_manager):
        self.db = db

    async def login(self, username: str, password: str) -> dict:
        """Авторизация: поиск, проверка, выдача токена"""

        log.info(f"Попытка авторизации пользователя: {username}")

        # Поиск пользователя
        user = await self.db.users.get_by_username(username)

        # Проверка пароля
        if not user or not verify_password(password, user.hashed_password):
            log.warning(f"Отказ в доступе. Неверный логин или пароль для пользователя: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Выдача токена
        log.info(f"Пользователь '{username}' успешно авторизован.")
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
