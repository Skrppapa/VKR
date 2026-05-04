from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from src.repositories.base import BaseRepository
from src.models.repair_stages import RepairStage
from src.models.stage_parts import StagePart
from src.schemas.repair_stages import RepairStageCreate, RepairStageUpdate


class RepairStageRepository(BaseRepository[RepairStage, RepairStageCreate, RepairStageUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(RepairStage, session)

    async def get_with_resources(self, stage_id: int) -> Optional[RepairStage]:
        """Получить этап со всеми привязанными ресурсами"""
        query = (
            select(self.model)
            .where(self.model.id == stage_id)
            .options(
                selectinload(self.model.brigades),
                # Тянем связь с запчастями и сразу подгружаем саму деталь
                selectinload(self.model.part_associations).selectinload(StagePart.part)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()