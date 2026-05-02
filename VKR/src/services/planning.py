from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from src.models import RollingStock, Regulation, RepairTask
from src.models.enums import TaskStatusEnum


class PlanningService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_train_planning_status(self, train_id: int):
        """Вычисляет статусы по всем видам ремонта для конкретного поезда."""

        # 1. Получаем поезд
        train = await self.session.get(RollingStock, train_id)
        if not train:
            return None

        # 2. Получаем все регламенты для этой серии поезда
        reg_query = select(Regulation).where(Regulation.train_series == train.series)
        regulations = (await self.session.execute(reg_query)).scalars().all()

        planning_results = []
        now = datetime.now(timezone.utc)

        for reg in regulations:
            # 3. Ищем последнюю завершенную задачу по этому виду ремонта
            task_query = (
                select(func.max(RepairTask.actual_end_date))
                .where(
                    RepairTask.rolling_stock_id == train.id,
                    RepairTask.repair_type == reg.repair_type,
                    RepairTask.status == TaskStatusEnum.COMPLETED
                )
            )
            last_repair_date = (await self.session.execute(task_query)).scalar()

            if not last_repair_date:
                # Если ремонта еще не было, считаем от даты выпуска поезда
                # manufacture_date - это date, переводим в datetime с timezone
                base_date = datetime.combine(train.manufacture_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            else:
                base_date = last_repair_date

            # Вычисляем дедлайн и оставшиеся дни
            next_repair_date = base_date + timedelta(days=reg.frequency_days)
            days_remaining = (next_repair_date - now).days

            planning_results.append({
                "repair_type": reg.repair_type,
                "last_repair_date": last_repair_date,
                "next_repair_date": next_repair_date,
                "days_remaining": days_remaining,
                "is_overdue": days_remaining < 0
            })

        return {
            "inventory_number": train.inventory_number,
            "series": train.series,
            "planning": planning_results
        }