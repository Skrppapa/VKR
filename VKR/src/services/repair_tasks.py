from fastapi import HTTPException, status
from src.models import RepairStage
from src.schemas.repair_tasks import RepairTaskCreate
from src.models.repair_tasks import RepairTask
from src.models.enums import TaskStatusEnum, StageStatusEnum
from src.utils.db_manager import DBManager


class RepairTaskService:
    def __init__(self, db: DBManager):
        self.db = db

    async def get_all_active(self):
        """Получить все активные задачи"""
        return await self.db.tasks.get_active_tasks()

    async def get_full_task(self, task_id: int):
        """Получить полную задачу с этапами по ID"""
        task = await self.db.tasks.get_full_task_graph(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")
        return task

    async def create_task(self, task_in: RepairTaskCreate) -> RepairTask:
        """Создание нового задания"""

        # Забираем серию поезда
        train = await self.db.trains.get_by_id(task_in.rolling_stock_id)
        if not train:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="МВПС не найден")

        # Забираем регламент
        reg = await self.db.regulations.get_by_type_and_series(
            repair_type=task_in.repair_type,
            train_series=train.series
        )

        if not reg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не найден регламент для {task_in.repair_type.value} и серии {train.series}. Невозможно сгенерировать этапы."
            )

        # Создаем задание (внутри репозитория делается flush, поэтому new_task уже имеет id)
        new_task = await self.db.tasks.create(task_in)

        # 4. Добавление этапов в созданное задание
        if reg.templates:
            for template in sorted(reg.templates, key=lambda x: x.order_number):
                new_stage = RepairStage(
                    repair_task_id=new_task.id,
                    regulation_id=reg.id,
                    name=template.name,
                    status=StageStatusEnum.PENDING
                )
                # Добавляем новый этап в сессию через наш DBManager
                self.db.session.add(new_stage)

        # Сохраняем ID до коммита (избегаем MissingGreenlet ошибки)
        task_id = new_task.id

        # Коммитим транзакцию (new_task становится expired, а этапы сохраняются в БД)
        await self.db.commit()

        # Возвращаем свежий объект из БД (вместе со связанными этапами, если настроен selectinload)
        return await self.db.tasks.get_by_id(task_id)

    async def delete_task(self, task_id: int):
        """Удалить задание"""
        task = await self.db.tasks.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")

        if task.status in [TaskStatusEnum.IN_PROGRESS, TaskStatusEnum.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить задание, которое уже выполняется или завершено."
            )

        await self.db.tasks.delete(task_id)
        await self.db.commit()

    async def get_archived_tasks(self, skip: int = 0, limit: int = 100):
        """Получить завершенные задания (Архив)"""
        return await self.db.tasks.get_archived_tasks(skip=skip, limit=limit)