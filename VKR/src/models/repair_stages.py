from src.database import Base
from src.models.enums import StageStatusEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Enum, String, Table, Column, Integer
from typing import Optional
import datetime


# Промежуточные таблицы
# Для связи Этап - Бригада
stage_brigade_association = Table(
    "stage_brigade_association",
    Base.metadata,
    Column("stage_id", Integer, ForeignKey("repair_stages.id"), primary_key=True),
    Column("brigade_id", Integer, ForeignKey("work_brigades.id"), primary_key=True),
    Column("role", String(100), nullable=True)  # Роль бригады/сотрудника в задаче
)

# Для связи Этап - Запчасти
stage_part_association = Table(
    "stage_part_association",
    Base.metadata,
    Column("stage_id", Integer, ForeignKey("repair_stages.id"), primary_key=True),
    Column("part_id", Integer, ForeignKey("parts_and_materials.id"), primary_key=True),
    Column("quantity_used", Integer, default=1)  # Сколько деталей списано на этап
)


class RepairStage(Base):
    """Этап ремонта"""
    __tablename__ = "repair_stages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    repair_task_id: Mapped[int] = mapped_column(ForeignKey("repair_tasks.id"))
    regulation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regulations.id"), nullable=True)

    name: Mapped[str] = mapped_column(String(100))  # Диагностика, разборка, сборка и т.д.
    status: Mapped[StageStatusEnum] = mapped_column(Enum(StageStatusEnum),
                                                    default=StageStatusEnum.PENDING)  # Умный таймер и статусы

    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    repair_task: Mapped["RepairTask"] = relationship(back_populates="stages")
    regulation: Mapped["Regulation"] = relationship(back_populates="stages")

    # M:N связи
    brigades: Mapped[list["WorkBrigade"]] = relationship(secondary=stage_brigade_association, back_populates="stages")
    parts: Mapped[list["PartAndMaterial"]] = relationship(secondary=stage_part_association, back_populates="stages")