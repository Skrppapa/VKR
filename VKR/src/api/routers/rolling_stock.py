from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies import get_db_session
from src.schemas.rolling_stocks import RollingStockCreate, RollingStockResponse,RollingStockUpdate
from src.services.rolling_stock import RollingStockService


router = APIRouter(prefix="/rolling-stocks", tags=["МВПС (Поезда)"])

@router.get("/", response_model=List[RollingStockResponse])
async def get_rolling_stocks(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session)
):
    """Получить список всех поездов."""
    service = RollingStockService(session)
    return await service.get_all_trains(skip=skip, limit=limit)

@router.get("/{train_id}", response_model=RollingStockResponse)
async def get_rolling_stock(
    train_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Получить информацию о конкретном поезде по ID."""
    service = RollingStockService(session)
    return await service.get_train_by_id(train_id)

@router.post("/", response_model=RollingStockResponse, status_code=status.HTTP_201_CREATED)
async def create_rolling_stock(
    train_in: RollingStockCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Регистрация нового поезда в системе."""
    service = RollingStockService(session)
    return await service.create_train(train_in)

@router.patch("/{train_id}", response_model=RollingStockResponse)
async def update_rolling_stock(
    train_id: int,
    update_data: RollingStockUpdate,
    session: AsyncSession = Depends(get_db_session)
):
    """Частичное обновление данных о поезде (например, исправление опечатки)."""
    service = RollingStockService(session)
    return await service.update_train(train_id, update_data)

@router.delete("/{train_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rolling_stock(
    train_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Удалить информацию о поезде из системы."""
    service = RollingStockService(session)
    await service.delete_train(train_id)
    return None