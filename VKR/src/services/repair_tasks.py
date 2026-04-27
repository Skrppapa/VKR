from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime, timezone
from src.repositories.repair_tasks import RepairTaskRepository
from src.schemas.repair_tasks import RepairTaskCreate, TaskStatusPatch
from src.models.repair_tasks import RepairTask
from src.models.enums import TaskStatusEnum, StageStatusEnum

class RepairTaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RepairTaskRepository(session)

    async def create_task(self, task_in: RepairTaskCreate) -> RepairTask:
        new_task = await self.repo.create(task_in)
        await self.session.commit()
        return new_task

    async def get_all_active(self):
        return await self.repo.get_active_tasks()

    async def get_full_task(self, task_id: int):
        task = await self.repo.get_full_task_graph(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задание не найдено")
        return task

    async def update_task_status(self, task_id: int, status_data: TaskStatusPatch) -> RepairTask:
        """Смена статуса ремонтного задания с проверкой вложенных этапов."""
        # Используем наш мощный метод загрузки графа, чтобы увидеть все этапы
        task = await self.repo.get_full_task_graph(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")

        new_status = status_data.status

        # Защитная логика: Попытка завершить ремонт
        if new_status == TaskStatusEnum.COMPLETED:
            # Проверяем, есть ли этапы, которые еще не завершены
            incomplete_stages = [s for s in task.stages if s.status != StageStatusEnum.COMPLETED]
            if incomplete_stages:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Невозможно завершить задание. Осталось незавершенных этапов: {len(incomplete_stages)}"
                )
            # Если всё ок, фиксируем фактическое время завершения
            task.actual_end_date = datetime.now(timezone.utc)

        # Логика: Перевод "В работу" (если ранее было "Создано" или "Ожидание")
        elif new_status == TaskStatusEnum.IN_PROGRESS and not task.start_date:
            task.start_date = datetime.now(timezone.utc)

        # Обновляем сам статус
        task.status = new_status
        await self.repo.update(task, {"status": new_status, "actual_end_date": task.actual_end_date})
        await self.session.commit()

        return task

    # async def update_task(self, task_id: int, update_data: RepairTaskUpdate):
    #     task = await self.repo.get_by_id(task_id)
    #     if not task: raise HTTPException(404, "Задание не найдено")
    #     updated_task = await self.repo.update(task, update_data)
    #     await self.session.commit()
    #     return updated_task

    async def delete_task(self, task_id: int):
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")

        # ЗАЩИТА ОТ УДАЛЕНИЯ АКТИВНЫХ И ЗАВЕРШЕННЫХ ЗАДАНИЙ
        if task.status in [TaskStatusEnum.IN_PROGRESS, TaskStatusEnum.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить задание, которое уже выполняется или завершено."
            )

        await self.repo.delete(task_id)
        await self.session.commit()

