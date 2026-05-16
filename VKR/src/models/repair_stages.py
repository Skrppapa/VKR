from src.database import Base, int_pk
from src.models.enums import StageStatusEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Enum, String, Table, Column, Integer
from typing import Optional
import datetime

# Промежуточная таблица для связи с бригадой
stage_brigade_association = Table(
    "stage_brigade_association",
    Base.metadata,
    Column("stage_id", Integer, ForeignKey("repair_stages.id"), primary_key=True),
    Column("brigade_id", Integer, ForeignKey("work_brigades.id"), primary_key=True),
    Column("role", String(100), nullable=True)
)

class RepairStage(Base):
    """Этап ремонта"""
    __tablename__ = "repair_stages"

    id: Mapped[int_pk]
    repair_task_id: Mapped[int] = mapped_column(ForeignKey("repair_tasks.id", ondelete="CASCADE"))
    regulation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regulations.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[StageStatusEnum] = mapped_column(Enum(StageStatusEnum), default=StageStatusEnum.PENDING)
    start_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Таймер и паузы
    last_paused_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_paused_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pause_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    repair_task: Mapped["RepairTask"] = relationship(back_populates="stages")
    regulation: Mapped["Regulation"] = relationship(back_populates="stages")

    brigades: Mapped[list["WorkBrigade"]] = relationship(secondary=stage_brigade_association, back_populates="stages")
    part_associations: Mapped[list["StagePart"]] = relationship(
        back_populates="stage",
        cascade="all, delete-orphan"
    )

    def __str__(self):
        return self.name