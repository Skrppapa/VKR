from src.database import Base, int_pk
from src.models.enums import RepairTypeEnum, TaskStatusEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Enum, Integer
from typing import Optional
import datetime

class RepairTask(Base):
    """Ремонтное задание"""
    __tablename__ = "repair_tasks"

    id: Mapped[int_pk]
    rolling_stock_id: Mapped[int] = mapped_column(ForeignKey("rolling_stocks.id"))
    repair_type: Mapped[RepairTypeEnum] = mapped_column(Enum(RepairTypeEnum))
    status: Mapped[TaskStatusEnum] = mapped_column(Enum(TaskStatusEnum), default=TaskStatusEnum.CREATED)
    start_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_paused_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    rolling_stock: Mapped["RollingStock"] = relationship(back_populates="repair_tasks")
    stages: Mapped[list["RepairStage"]] = relationship(back_populates="repair_task", cascade="all, delete-orphan")