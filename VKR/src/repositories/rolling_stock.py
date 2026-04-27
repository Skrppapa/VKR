from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional

from src.repositories.base import BaseRepository
from src.models.rolling_stocks import RollingStock
from src.schemas.rolling_stocks import RollingStockCreate, RollingStockUpdate

class RollingStockRepository(BaseRepository[RollingStock, RollingStockCreate, RollingStockUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(RollingStock, session)

    async def get_by_inventory_number(self, inv_number: str) -> Optional[RollingStock]:
        query = select(self.model).where(self.model.inventory_number == inv_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_tasks(self, obj_id: int) -> Optional[RollingStock]:
        """Достать МВПС сразу с его ремонтными заданиями"""
        query = (
            select(self.model)
            .where(self.model.id == obj_id)
            .options(selectinload(self.model.repair_tasks))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()