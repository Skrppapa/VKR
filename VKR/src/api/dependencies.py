from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import async_session_maker

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор сессий БД для FastAPI Depends.
    Обеспечивает создание новой сессии на каждый запрос и её безопасное закрытие.
    """
    async with async_session_maker() as session:
        try:
            yield session
            # Мы не делаем здесь автоматический commit,
            # потому что при ошибке валидации или бизнес-логики
            # мы хотим, чтобы транзакция откатилась (rollback).
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()