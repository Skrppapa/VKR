from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from src.repositories.base import BaseRepository
from src.models.repair_tasks import RepairTask
from src.models.repair_stages import RepairStage
from src.models.stage_parts import StagePart
from src.schemas.repair_tasks import RepairTaskCreate, TaskStatusPatch
from src.models.enums import TaskStatusEnum

class RepairTaskRepository(BaseRepository[RepairTask, RepairTaskCreate, TaskStatusPatch]):
    def __init__(self, session: AsyncSession):
        super().__init__(RepairTask, session)

    async def get_active_tasks(self) -> List[RepairTask]:
        """Получить все незавершенные задания."""
        query = select(self.model).where(self.model.status != TaskStatusEnum.COMPLETED)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_full_task_graph(self, task_id: int) -> Optional[RepairTask]:
        """Достать задание со всеми этапами, бригадами и деталями."""
        query = (
            select(self.model)
            .where(self.model.id == task_id)
            .options(
                selectinload(self.model.stages).selectinload(RepairStage.brigades),
                selectinload(self.model.stages).selectinload(RepairStage.part_associations).selectinload(StagePart.part)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()