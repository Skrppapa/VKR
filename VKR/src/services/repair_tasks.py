from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.models import RepairStage
from src.repositories.catalogs import RegulationRepository
from src.repositories.repair_tasks import RepairTaskRepository
from src.repositories.rolling_stock import RollingStockRepository
from src.schemas.repair_tasks import RepairTaskCreate
from src.models.repair_tasks import RepairTask
from src.models.enums import TaskStatusEnum, StageStatusEnum


class RepairTaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RepairTaskRepository(session)
        self.train_repo = RollingStockRepository(session)
        self.reg_repo = RegulationRepository(session)

    async def get_all_active(self):
        """Получить все активные задачи"""
        return await self.repo.get_active_tasks()

    async def get_full_task(self, task_id: int):
        """Получить полную задачу с этапами по ID"""
        task = await self.repo.get_full_task_graph(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")
        return task

    async def create_task(self, task_in: RepairTaskCreate) -> RepairTask:
        """Создание нового задания"""

        # Забираем серию поезда
        train = await self.train_repo.get_by_id(task_in.rolling_stock_id)
        if not train:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="МВПС не найден")

        # Забираем регламент
        reg = await self.reg_repo.get_by_type_and_series(
            repair_type=task_in.repair_type,
            train_series=train.series
        )

        if not reg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не найден регламент для {task_in.repair_type.value} и серии {train.series}. Невозможно сгенерировать этапы."
            )

        # Создаем задание
        new_task = await self.repo.create(task_in)

        # 4. Добавление этапов в созданное задание
        if reg.templates:
            for template in sorted(reg.templates, key=lambda x: x.order_number):
                new_stage = RepairStage(
                    repair_task_id=new_task.id,
                    regulation_id=reg.id,
                    name=template.name,
                    status=StageStatusEnum.PENDING
                )
                self.session.add(new_stage)

        # Сохраняем ID до коммита
        task_id = new_task.id

        # Коммитим транзакцию (new_task становится expired)
        await self.session.commit()

        # Возвращаем свежий объект из БД
        return await self.repo.get_by_id(task_id)

    async def delete_task(self, task_id: int):
        """Удалить задание"""
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")

        if task.status in [TaskStatusEnum.IN_PROGRESS, TaskStatusEnum.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить задание, которое уже выполняется или завершено."
            )

        await self.repo.delete(task_id)
        await self.session.commit()

    async def get_archived_tasks(self, skip: int = 0, limit: int = 100):
        """Получить завершенные задания (Архив)"""
        return await self.repo.get_archived_tasks(skip=skip, limit=limit)
