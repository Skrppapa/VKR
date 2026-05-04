from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from src.utils.db_manager import DBManager


class PlanningService:
    def __init__(self, db: DBManager):
        self.db = db

    async def get_train_planning_status(self, train_id: int):
        """Вычисление статусов по всем видам ремонта для конкретного поезда"""

        # Получаем поезд
        train = await self.db.trains.get_by_id(train_id)

        if not train:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="МВПС не найден"
            )

        # Получаем все регламенты для этой серии
        regulations = await self.db.regulations.get_all_by_series(train.series)

        planning_results = []
        now = datetime.now(timezone.utc)

        for reg in regulations:
            # Ищем последнюю завершенную задачу через репозиторий
            last_repair_date = await self.db.tasks.get_last_completed_date(
                train_id=train.id,
                repair_type=reg.repair_type
            )

            if not last_repair_date:
                # Если ремонта еще не было, считаем от даты выпуска поезда
                base_date = datetime.combine(train.manufacture_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            else:
                base_date = last_repair_date

            # Вычисляем оставшиеся дни
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