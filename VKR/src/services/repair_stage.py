from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.repositories.repair_stage import RepairStageRepository
from src.repositories.catalogs import PartRepository
from src.schemas.repair_stages import RepairStageCreate
from src.models.repair_stages import RepairStage
from src.models.stage_parts import StagePart
from datetime import datetime, timezone
from src.models.enums import StageStatusEnum
from src.schemas.repair_stages import StageStatusPatch, RepairStageUpdate


class RepairStageService:
    def __init__(self, session: AsyncSession):
        self.session = session
        # Если нет отдельного репозитория, используем базовый
        self.stage_repo = RepairStageRepository(session)
        self.part_repo = PartRepository(session)

    async def create_stage(self, stage_in: RepairStageCreate):
        stage = await self.stage_repo.create(stage_in)
        await self.session.commit()
        return stage

    async def assign_part_to_stage(self, stage_id: int, part_id: int, quantity: int):
        """Списание детали со склада и привязка к этапу."""

        # 1. Проверяем наличие этапа
        stage = await self.stage_repo.get_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Этап не найден")

        # 2. Проверяем наличие детали на складе
        part = await self.part_repo.get_by_id(part_id)
        if not part:
            raise HTTPException(status_code=404, detail="Деталь не найдена в базе")

        if part.stock_quantity < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно деталей на складе. Доступно: {part.stock_quantity}, запрошено: {quantity}"
            )

        # 3. Списываем со склада (обновляем остаток)
        part.stock_quantity -= quantity
        self.session.add(part)  # Сохраняем изменение детали

        # 4. Создаем связь StagePart
        stage_part = StagePart(stage_id=stage_id, part_id=part_id, quantity_used=quantity)
        self.session.add(stage_part)

        # 5. Фиксируем транзакцию (списание и привязка происходят ОДНОВРЕМЕННО)
        await self.session.commit()
        return {"message": "Детали успешно списаны и привязаны к этапу"}

    async def update_stage_status(self, stage_id: int, status_data: StageStatusPatch) -> RepairStage:
        """Смена статуса этапа с автоматической фиксацией времени."""
        stage = await self.stage_repo.get_by_id(stage_id)
        if not stage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Этап не найден")

        new_status = status_data.status

        # Логика 1: Переход "В работу"
        if new_status == StageStatusEnum.IN_PROGRESS and stage.status != StageStatusEnum.IN_PROGRESS:
            stage.start_time = datetime.now(timezone.utc)

        # Логика 2: Переход "Завершено"
        elif new_status == StageStatusEnum.COMPLETED and stage.status != StageStatusEnum.COMPLETED:
            stage.end_time = datetime.now(timezone.utc)
            # Если завершили без начала (например, быстрая отметка), ставим старт тем же временем
            if not stage.start_time:
                stage.start_time = stage.end_time

        # Обновляем статус
        stage.status = new_status

        # Передаем обновленный объект в репозиторий (он сам сделает session.add)
        await self.stage_repo.update(stage,
                                     {"status": new_status, "start_time": stage.start_time, "end_time": stage.end_time})

        # Коммитим транзакцию
        await self.session.commit()
        return stage

    async def update_stage(self, stage_id: int, update_data: RepairStageUpdate):
        stage = await self.stage_repo.get_by_id(stage_id)
        if not stage: raise HTTPException(404, "Этап не найден")
        updated_stage = await self.stage_repo.update(stage, update_data)
        await self.session.commit()
        return updated_stage

    async def delete_stage(self, stage_id: int):
        await self.stage_repo.delete(stage_id)
        await self.session.commit()