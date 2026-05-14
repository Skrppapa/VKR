from src.database import Base, int_pk
from src.models.enums import RepairTypeEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, UniqueConstraint


class Regulation(Base):
    """Регламент"""
    __tablename__ = "regulations"

    id: Mapped[int_pk]
    repair_type: Mapped[RepairTypeEnum] = mapped_column(nullable=False)
    train_series: Mapped[str] = mapped_column(String(50), nullable=False)
    standard_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    frequency_days: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    stages: Mapped[list["RepairStage"]] = relationship(back_populates="regulation")
    templates: Mapped[list["RegulationStageTemplate"]] = relationship(back_populates="regulation", cascade="all, delete-orphan")

    # Уникальность из двух столбцов Тип ремонта (repair_type) и Модель поезда (train_series)
    __table_args__ = (
        UniqueConstraint("repair_type", "train_series", name="uq_repair_type_train_series"),
    )
