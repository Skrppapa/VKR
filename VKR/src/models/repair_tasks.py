from src.database import Base
from src.models.enums import RepairTypeEnum, TaskStatusEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from typing import Optional
import datetime


class RepairTask(Base):
    """Ремонтное задание"""
    __tablename__ = "repair_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rolling_stock_id: Mapped[int] = mapped_column(ForeignKey("rolling_stocks.id"))

    repair_type: Mapped[RepairTypeEnum] = mapped_column(Enum(RepairTypeEnum))  # Вид ремонта
    status: Mapped[TaskStatusEnum] = mapped_column(Enum(TaskStatusEnum),
                                                   default=TaskStatusEnum.CREATED)  # Текущий статус

    start_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    planned_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    rolling_stock: Mapped["RollingStock"] = relationship(back_populates="repair_tasks")
    # Задание разбивается на этапы
    stages: Mapped[list["RepairStage"]] = relationship(back_populates="repair_task", cascade="all, delete-orphan")
