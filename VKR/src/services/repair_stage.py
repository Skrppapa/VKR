from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from src.models.repair_stages import RepairStage
from src.models.stage_parts import StagePart
from src.models.enums import StageStatusEnum, TaskStatusEnum
from src.schemas.repair_stages import StageStatusPatch
from src.repositories.repair_stage import RepairStageRepository
from src.repositories.catalogs import PartRepository, RegulationRepository
from src.repositories.repair_tasks import RepairTaskRepository


class RepairStageService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stage_repo = RepairStageRepository(session)
        self.part_repo = PartRepository(session)
        self.task_repo = RepairTaskRepository(session)
        self.reg_repo = RegulationRepository(session)

    async def assign_part_to_stage(self, stage_id: int, part_id: int, quantity: int):
        """Списание детали со склада и привязка к этапу."""

        stage = await self.stage_repo.get_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Этап не найден")

        part = await self.part_repo.get_by_id(part_id)
        if not part:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Деталь не найдена в базе")

        if part.stock_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно деталей на складе. Доступно: {part.stock_quantity}, запрошено: {quantity}"
            )

        part.stock_quantity -= quantity
        self.session.add(part)

        stage_part = StagePart(stage_id=stage_id, part_id=part_id, quantity_used=quantity)
        self.session.add(stage_part)

        await self.session.commit()
        return {"message": "Детали успешно списаны и привязаны к этапу"}

    async def update_stage_status(self, stage_id: int, status_data: StageStatusPatch) -> RepairStage:
        """Обновление статуса этапа"""

        stage = await self.stage_repo.get_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Этап не найден")

        task = await self.task_repo.get_with_stages(stage.repair_task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Родительское задание не найдено")

        task_stages = sorted(task.stages, key=lambda s: s.id)
        current_index = next(i for i, s in enumerate(task_stages) if s.id == stage.id)

        new_status = status_data.status
        old_status = stage.status

        if new_status == old_status:
            return stage

        # Ожидание запчастей или пауза
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
                    reg = await self.reg_repo.get_by_id(stage.regulation_id)
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
        self.session.add(stage)
        self.session.add(task)
        await self.session.commit()

        return stage
