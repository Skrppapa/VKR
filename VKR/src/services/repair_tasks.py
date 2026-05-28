from datetime import datetime, timezone
import os
import shutil
from fastapi import HTTPException, status, UploadFile
from src.models import RepairStage
from src.schemas.repair_tasks import RepairTaskCreate
from src.models.repair_tasks import RepairTask
from src.models.enums import TaskStatusEnum, StageStatusEnum
from src.utils.db_manager import DBManager
from src.utils.logger import log




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
            raise HTTPException(404, "Задание не найдено")
        return task

    async def create_task(self, task_in: RepairTaskCreate) -> RepairTask:
        """Создание нового задания с привязкой к бригаде и генерацией этапов"""

        train = await self.db.trains.get_by_id(task_in.rolling_stock_id)
        if not train:
            raise HTTPException(404, "МВПС не найден")

        brigade = await self.db.brigades.get_by_id(task_in.brigade_id)
        if not brigade:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанная бригада не существует. Невозможно назначить задание."
            )

        reg = await self.db.regulations.get_by_type_and_series(
            repair_type=task_in.repair_type,
            train_series=train.series
        )

        if not reg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не найден регламент для {task_in.repair_type.value} и серии {train.series}. Невозможно сгенерировать этапы."
            )

        task_data = task_in.model_dump()
        task_data["master_name_snapshot"] = brigade.master_name

        new_task = await self.db.tasks.create(task_data)

        if reg.templates:
            for template in sorted(reg.templates, key=lambda x: x.order_number):
                new_stage = RepairStage(
                    repair_task_id=new_task.id,
                    regulation_id=reg.id,
                    name=template.name,
                    status=StageStatusEnum.PENDING
                )
                self.db.session.add(new_stage)

        task_id = new_task.id

        await self.db.commit()

        log.info(
            f"Создано задание ID {task_id} ({task_in.repair_type.value}) для МВПС {train.series} ({train.inventory_number}). Назначена бригада: {brigade.name}")

        return await self.db.tasks.get_task_with_train(task_id)



    async def delete_task(self, task_id: int):
        """Удалить задание"""
        log.info(f"Попытка удаления задания ID: {task_id}")

        task = await self.db.tasks.get_by_id(task_id)
        if not task:
            log.warning(f"Задание ID: {task_id} не найдено для удаления")
            raise HTTPException(404, "Задание не найдено")

        if task.status in [TaskStatusEnum.IN_PROGRESS, TaskStatusEnum.COMPLETED]:
            log.warning(
                f"Отказ в удалении задания {task_id}. Текущий статус: {task.status.name if hasattr(task.status, 'name') else task.status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить задание, которое уже выполняется или завершено."
            )

        await self.db.tasks.delete(task_id)
        await self.db.commit()
        log.info(f"Задание ID: {task_id} успешно удалено из БД")

        await self.db.tasks.delete(task_id)
        await self.db.commit()

    async def get_archived_tasks(self, skip: int = 0, limit: int = 100):
        """Получить завершенные задания (Архив)"""
        return await self.db.tasks.get_archived_tasks(skip=skip, limit=limit)

    async def submit_for_closure(self, task_id: int, file: UploadFile):
        """Мастер отправляет задание на проверку с актом"""
        task = await self.db.tasks.get_with_stages(task_id)
        if not task:
            raise HTTPException(404, "Задание не найдено")

        # Проверяем, что все этапы завершены (базовая валидация)
        incomplete_stages = [s for s in task.stages if s.status != StageStatusEnum.COMPLETED]
        if incomplete_stages:
            raise HTTPException(400, "Не все этапы завершены. Закрытие невозможно.")

        # Сохраняем файл (для ВКР достаточно локальной папки media/docs)
        os.makedirs("media/docs", exist_ok=True)
        file_path = f"media/docs/task_{task_id}_{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        task.closure_document_path = file_path
        task.status = TaskStatusEnum.PENDING_CLOSURE
        task.inspector_comment = None  # Очищаем старые комментарии, если это повторная подача

        await self.db.commit()
        return await self.db.tasks.get_task_with_train(task_id)

    async def approve_closure(self, task_id: int):
        """Диспетчер принимает работу"""
        task = await self.db.tasks.get_by_id(task_id)
        if not task or task.status != TaskStatusEnum.PENDING_CLOSURE:
            raise HTTPException(400, "Задание не найдено или не в статусе ожидания закрытия")

        task.status = TaskStatusEnum.COMPLETED
        task.actual_end_date = datetime.now(timezone.utc)
        await self.db.commit()
        return task

    async def reject_closure(self, task_id: int, comment: str):
        """Диспетчер отклоняет работу"""
        task = await self.db.tasks.get_with_stages(task_id)
        if not task or task.status != TaskStatusEnum.PENDING_CLOSURE:
            raise HTTPException(400, "Задание не в статусе проверки")

        task.status = TaskStatusEnum.IN_PROGRESS
        task.inspector_comment = comment

        # Откатываем последний этап обратно в работу
        if task.stages:
            stages_sorted = sorted(task.stages, key=lambda s: s.id)
            last_stage = stages_sorted[-1]
            last_stage.status = StageStatusEnum.IN_PROGRESS
            last_stage.end_time = None  # Сбрасываем время завершения этапа

        await self.db.commit()
        return task