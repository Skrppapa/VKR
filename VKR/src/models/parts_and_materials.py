from src.database import Base, int_pk
from src.models.repair_stages import stage_part_association
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer


class PartAndMaterial(Base):
    """Запчасти и материалы"""
    __tablename__ = "parts_and_materials"

    id: Mapped[int_pk]
    nomenclature: Mapped[str] = mapped_column(String(150), unique=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)  # Проверка наличия на складе

    stages: Mapped[list["RepairStage"]] = relationship(secondary=stage_part_association, back_populates="parts")