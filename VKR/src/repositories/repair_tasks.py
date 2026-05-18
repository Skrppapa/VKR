from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from src.models.enums import TaskStatusEnum
from datetime import datetime
from src.repositories.base import BaseRepository
from src.models.repair_tasks import RepairTask
from src.models.repair_stages import RepairStage
from src.models.stage_parts import StagePart
from src.schemas.repair_tasks import RepairTaskCreate, TaskStatusPatch


class RepairTaskRepository(BaseRepository[RepairTask, RepairTaskCreate, TaskStatusPatch]):
    def __init__(self, session: AsyncSession):
        super().__init__(RepairTask, session)

    async def get_active_tasks(self) -> list[RepairTask]:
        """Получить все активные задания"""
        query = (
            select(self.model)
            .where(self.model.status != TaskStatusEnum.COMPLETED)
            .options(selectinload(self.model.rolling_stock))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_full_task_graph(self, task_id: int) -> Optional[RepairTask]:
        """Достать задание со всеми этапами, бригадами и деталями"""
        query = (
            select(self.model)
            .where(self.model.id == task_id)
            .options(
                selectinload(self.model.rolling_stock),
                selectinload(self.model.brigade),
                selectinload(self.model.stages).selectinload(RepairStage.brigades),
                selectinload(self.model.stages).selectinload(RepairStage.part_associations).selectinload(StagePart.part)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_stages(self, task_id: int) -> Optional[RepairTask]:
        """Достать задание только с его этапами"""
        query = (
            select(self.model)
            .where(self.model.id == task_id)
            .options(selectinload(self.model.stages))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_archived_tasks(self, skip: int = 0, limit: int = 100) -> list[RepairTask]:
        """Получить завершенные задания (Архив)"""
        query = select(self.model).where(
            self.model.status == TaskStatusEnum.COMPLETED
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_last_completed_date(self, train_id: int, repair_type: TaskStatusEnum) -> Optional[datetime]:
        """Найти дату завершения последнего ремонта указанного типа для поезда"""
        query = (
            select(func.max(self.model.actual_end_date))
            .where(
                self.model.rolling_stock_id == train_id,
                self.model.repair_type == repair_type,
                self.model.status == TaskStatusEnum.COMPLETED
            )
        )
        result = await self.session.execute(query)
        return result.scalar()

