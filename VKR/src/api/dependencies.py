from typing import Annotated
from fastapi import Depends
from src.database import async_session_maker
from src.utils.db_manager import DBManager
from src.services.auth import AuthService


# Управление БД
async def get_db():
    async with DBManager(session_factory=async_session_maker) as db:
        yield db

DBDep = Annotated[DBManager, Depends(get_db)]

def get_auth_service(db: DBDep) -> AuthService:
    return AuthService(db)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
