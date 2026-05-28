from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from src.repositories.base import BaseRepository
from src.models.rolling_stocks import RollingStock
from src.schemas.rolling_stocks import RollingStockCreate, RollingStockUpdate

class RollingStockRepository(BaseRepository[RollingStock, RollingStockCreate, RollingStockUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(RollingStock, session)

    async def get_by_inventory_number(self, inv_number: str) -> Optional[RollingStock]:
        """Достать МВПС по инвентарному номеру"""
        query = select(self.model).where(self.model.inventory_number == inv_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def check_series_exists(self, series: str) -> bool:
        """Есть ли хоть один поезд указанной серии"""
        query = select(self.model).where(self.model.series == series).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_unique_series(self) -> list[str]:
        """Получить список уникальных серий МВПС"""
        query = select(self.model.series).distinct()
        result = await self.session.execute(query)
        return list(result.scalars().all())