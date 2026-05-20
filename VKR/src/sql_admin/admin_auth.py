from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from sqlalchemy import select
from src.database import async_session_maker
from src.models.users import User
from src.security import verify_password, create_access_token

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")

        async with async_session_maker() as session:
            query = select(User).where(User.username == username)
            user = (await session.execute(query)).scalar_one_or_none()

            # Проверяем существование пользователя и совпадение пароля
            if not user or not verify_password(password, user.hashed_password):
                return False

            # Строгая проверка роли: только admin имеет доступ к SqlAdmin
            if user.role != "admin":
                return False

            # Если всё ок — генерируем токен и кладем в сессию браузера
            access_token = create_access_token(data={"sub": user.username})
            request.session.update({"token": access_token})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True