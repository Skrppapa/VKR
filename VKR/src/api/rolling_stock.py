from fastapi import APIRouter, status, HTTPException
from src.api.dependencies import DBDep
from src.schemas.rolling_stocks import RollingStockCreate, RollingStockResponse,RollingStockUpdate
from src.services.rolling_stock import RollingStockService
from src.services.planning import PlanningService


router = APIRouter(prefix="/rolling-stocks", tags=["МВПС (Поезда)"])

@router.get("/", response_model=list[RollingStockResponse])
async def get_rolling_stocks(db: DBDep, skip: int = 0, limit: int = 100):
    """Получить список всех поездов."""
    service = RollingStockService(db)
    return await service.get_all_trains(skip=skip, limit=limit)

@router.get("/{train_id}", response_model=RollingStockResponse)
async def get_rolling_stock(train_id: int, db: DBDep):
    """Получить информацию о конкретном поезде по ID."""
    service = RollingStockService(db)
    return await service.get_train_by_id(train_id)

@router.post("/", response_model=RollingStockResponse, status_code=status.HTTP_201_CREATED)
async def create_rolling_stock(train_in: RollingStockCreate, db: DBDep):
    """Создание нового поезда"""
    service = RollingStockService(db)
    return await service.create_train(train_in)

@router.patch("/{train_id}", response_model=RollingStockResponse)
async def update_rolling_stock(train_id: int, update_data: RollingStockUpdate, db: DBDep):
    """Частичное обновление данных о поезде"""
    service = RollingStockService(db)
    return await service.update_train(train_id, update_data)

@router.delete("/{train_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rolling_stock(train_id: int, db: DBDep):
    """Удалить поезд"""
    service = RollingStockService(db)
    await service.delete_train(train_id)

@router.get("/{train_id}/planning")
async def get_train_planning(train_id: int, db: DBDep):
    """Получить план ремонтов для конкретного МВПС"""
    service = PlanningService(db)
    result = await service.get_train_planning_status(train_id)
    if not result:
        raise HTTPException(status_code=404, detail="МВПС не найден")
    return result