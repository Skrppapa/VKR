from fastapi import HTTPException, status
from src.schemas.rolling_stocks import RollingStockCreate, RollingStockUpdate
from src.models.rolling_stocks import RollingStock
from src.utils.db_manager import DBManager


class RollingStockService:
    def __init__(self, db: DBManager):
        self.db = db

    async def create_train(self, train_in: RollingStockCreate) -> RollingStock:
        # Проверка на дубликаты
        existing_train = await self.db.trains.get_by_inventory_number(train_in.inventory_number)
        if existing_train:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Поезд с номером {train_in.inventory_number} уже существует."
            )

        # Создание
        new_train = await self.db.trains.create(train_in)

        await self.db.commit()
        return new_train

    async def get_all_trains(self, skip: int = 0, limit: int = 100) -> list[RollingStock]:
        return await self.db.trains.get_all(skip=skip, limit=limit)

    async def get_train_by_id(self, train_id: int) -> RollingStock:
        train = await self.db.trains.get_by_id(train_id)
        if not train:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="МВПС не найден."
            )
        return train


    async def update_train(self, train_id: int, update_data: RollingStockUpdate) -> RollingStock:
        train = await self.db.trains.get_by_id(train_id)
        if not train:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="МВПС не найден")
        updated_train = await self.db.trains.update(train, update_data)
        await self.db.commit()
        return updated_train


    async def delete_train(self, train_id: int) -> None:
        train = await self.db.trains.get_by_id(train_id)
        if not train:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="МВПС не найден")
        await self.db.trains.delete(train_id)
        await self.db.commit()