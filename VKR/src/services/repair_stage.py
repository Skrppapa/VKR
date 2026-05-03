from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from src.models.repair_stages import RepairStage
from src.models.enums import StageStatusEnum, TaskStatusEnum
from src.schemas.repair_stages import StageStatusPatch
from src.utils.db_manager import DBManager


class RepairStageService:
    def __init__(self, db: DBManager):
        self.db = db

    async def add_part_to_repair_stage(self, stage_id: int, part_id: int, quantity: int):
        # 1. Проверяем существование этапа
        stage = await self.db.stages.get_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Этап не найден")

        # 2. Получаем деталь
        part = await self.db.parts.get_by_id(part_id)
        if not part:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Деталь не найдена")

        # 3. Валидация остатка (Бизнес-логика остается в сервисе)
        if part.stock_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно на складе. Доступно: {part.stock_quantity}, нужно: {quantity}"
            )

        # 4. Вызываем метод репозитория для выполнения механических действий (add, создание связи)
        await self.db.parts.use_part(part, quantity, stage_id)

        # 5. Фиксируем транзакцию одной командой
        await self.db.commit()


        await self.db.commit()
        return {"message": "Детали успешно списаны и привязаны к этапу"}

    async def update_stage_status(self, stage_id: int, status_data: StageStatusPatch) -> RepairStage:
        """Обновление статуса этапа"""

        stage = await self.db.stages.get_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Этап не найден")

        task = await self.db.tasks.get_with_stages(stage.repair_task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Родительское задание не найдено")

        task_stages = sorted(task.stages, key=lambda s: s.id)
        current_index = next(i for i, s in enumerate(task_stages) if s.id == stage.id)

        new_status = status_data.status
        old_status = stage.status

        if new_status == old_status:
            return stage

        # Ожидание запчастей или пауза

        new_status: StageStatusEnum = status_data.status
        old_status: StageStatusEnum = stage.status

        if new_status in [StageStatusEnum.PAUSED, StageStatusEnum.WAITING_PARTS]:
            if new_status == StageStatusEnum.PAUSED and not status_data.pause_reason:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="При ручном переходе в паузу необходимо указать причину (pause_reason)."
                )

            stage.pause_reason = status_data.pause_reason
            stage.last_paused_at = datetime.now(timezone.utc)

            if new_status == StageStatusEnum.WAITING_PARTS:
                task.status = TaskStatusEnum.WAITING_PARTS
            else:
                task.status = TaskStatusEnum.PAUSED

        # Запуск этапа В работу
        elif new_status == StageStatusEnum.IN_PROGRESS:
            if current_index > 0:
                prev_stage = task_stages[current_index - 1]
                if prev_stage.status != StageStatusEnum.COMPLETED:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Нельзя начать этот этап. Предыдущий этап '{prev_stage.name}' не завершен."
                    )

            # Сценарий 1: Снятие с паузы
            if old_status in [StageStatusEnum.PAUSED, StageStatusEnum.WAITING_PARTS] and stage.last_paused_at:
                pause_duration = datetime.now(timezone.utc) - stage.last_paused_at
                seconds = int(pause_duration.total_seconds())

                stage.total_paused_seconds += seconds
                task.total_paused_seconds += seconds

                if task.planned_end_date:
                    task.planned_end_date += pause_duration

                stage.last_paused_at = None
                task.status = TaskStatusEnum.IN_PROGRESS

            # Сценарий 2: Первый старт этапа
            if not stage.start_time:
                stage.start_time = datetime.now(timezone.utc)

            # Если это самый первый этап всей задачи - стартуем Задание
            if current_index == 0 and not task.start_date:
                task.start_date = datetime.now(timezone.utc)
                task.status = TaskStatusEnum.IN_PROGRESS

                # Получаем норматив через репозиторий
                if stage.regulation_id:
                    reg = await self.db.regulations.get_by_id(stage.regulation_id)
                    if reg:
                        task.planned_end_date = task.start_date + timedelta(hours=reg.standard_hours)
            else:
                task.status = TaskStatusEnum.IN_PROGRESS

        # Завершение этапа
        elif new_status == StageStatusEnum.COMPLETED:
            if not stage.start_time:
                stage.start_time = datetime.now(timezone.utc)
            stage.end_time = datetime.now(timezone.utc)

            is_last_stage = (current_index == len(task_stages) - 1)
            if is_last_stage:
                task.status = TaskStatusEnum.COMPLETED
                task.actual_end_date = datetime.now(timezone.utc)

        stage.status = new_status
        await self.db.commit()

        return stage
