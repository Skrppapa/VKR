from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.repositories.rolling_stock import RollingStockRepository
from src.schemas.rolling_stocks import RollingStockCreate, RollingStockUpdate, RollingStockResponse
from src.models.rolling_stocks import RollingStock


class RollingStockService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RollingStockRepository(session)

    async def create_train(self, train_in: RollingStockCreate) -> RollingStock:
        # 1. Проверяем бизнес-правило: нет ли уже поезда с таким номером?
        existing_train = await self.repo.get_by_inventory_number(train_in.inventory_number)
        if existing_train:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Поезд с номером {train_in.inventory_number} уже существует."
            )

        # 2. Создаем через репозиторий
        new_train = await self.repo.create(train_in)

        # 3. Фиксируем изменения в БД
        await self.session.commit()
        return new_train

    async def get_all_trains(self, skip: int = 0, limit: int = 100) -> list[RollingStock]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_train_by_id(self, train_id: int) -> RollingStock:
        train = await self.repo.get_by_id(train_id)
        if not train:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="МВПС не найден."
            )
        return train


    async def update_train(self, train_id: int, update_data: RollingStockUpdate) -> RollingStock:
        train = await self.repo.get_by_id(train_id)
        if not train:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="МВПС не найден")

        # Репозиторий сам обновит только те поля, которые были переданы в JSON
        updated_train = await self.repo.update(train, update_data)
        await self.session.commit()
        return updated_train


    async def delete_train(self, train_id: int) -> None:
        train = await self.repo.get_by_id(train_id)
        if not train:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="МВПС не найден")

        await self.repo.delete(train_id)
        await self.session.commit()