from src.database import Base, int_pk
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer


class PartAndMaterial(Base):
    """Запчасти и материалы"""
    __tablename__ = "parts_and_materials"

    id: Mapped[int_pk]
    nomenclature: Mapped[str] = mapped_column(String(150), unique=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)  # Проверка наличия на складе

    stage_associations: Mapped[list["StagePart"]] = relationship(back_populates="part")