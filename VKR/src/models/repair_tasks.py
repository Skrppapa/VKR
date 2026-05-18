from src.database import Base, int_pk
from src.models.enums import RepairTypeEnum, TaskStatusEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Enum, Integer, String
from typing import Optional
import datetime

class RepairTask(Base):
    """Ремонтное задание"""
    __tablename__ = "repair_tasks"

    id: Mapped[int_pk]
    rolling_stock_id: Mapped[int] = mapped_column(ForeignKey("rolling_stocks.id"))
    brigade_id: Mapped[Optional[int]] = mapped_column(ForeignKey("work_brigades.id"), nullable=True)
    master_name_snapshot: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    repair_type: Mapped[RepairTypeEnum] = mapped_column(Enum(RepairTypeEnum))
    status: Mapped[TaskStatusEnum] = mapped_column(Enum(TaskStatusEnum), default=TaskStatusEnum.CREATED)
    start_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_paused_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


    rolling_stock: Mapped["RollingStock"] = relationship(back_populates="repair_tasks")
    brigade: Mapped[Optional["WorkBrigade"]] = relationship(back_populates="repair_tasks")
    stages: Mapped[list["RepairStage"]] = relationship(
        back_populates="repair_task",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


    @property
    def train_series(self) -> str:
        return self.rolling_stock.series if self.rolling_stock else "Неизвестно"

    @property
    def baseline_end_date(self):
        """Вычисление времени окончания по регламенту"""
        if not self.planned_end_date:
            return None

        # Если паузы есть, вычитаем их из текущего плана
        pauses = self.total_paused_seconds or 0
        return self.planned_end_date - datetime.timedelta(seconds=pauses)


    @property
    def formatted_paused_time(self) -> str:
        """Переводит секунды в читаемый формат: X ч Y мин"""
        if not self.total_paused_seconds:
            return "0 ч 0 мин"

        hours = self.total_paused_seconds // 3600
        minutes = (self.total_paused_seconds % 3600) // 60

        # Если пауза длилась меньше минуты
        if hours == 0 and minutes == 0 and self.total_paused_seconds > 0:
            return f"{self.total_paused_seconds} сек"

        return f"{hours} ч {minutes} мин"

    @property
    def overdue_hours(self) -> int:
        """Вычисляет количество часов просрочки"""
        if not self.planned_end_date:
            return 0

        # Сравниваем план с фактом завершения. Если еще в работе — с текущим временем
        end_time = self.actual_end_date if self.actual_end_date else datetime.datetime.now(datetime.timezone.utc)
        delta = end_time - self.planned_end_date

        if delta.total_seconds() > 0:
            return int(delta.total_seconds() / 3600)  # Возвращаем просрочку в часах
        return 0