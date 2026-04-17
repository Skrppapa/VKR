from src.database import Base, int_pk
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Date
from datetime import date


class RollingStock(Base):
    """Сущность МВПС"""
    __tablename__ = "rolling_stocks"

    id: Mapped[int_pk]
    inventory_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # Инвентарный номер
    series: Mapped[str] = mapped_column(String(50))  # Серийный номер
    manufacture_date: Mapped[date] = mapped_column(Date)  # Дата выпуска

    # Связь один-ко-многим: Один вагон имеет много ремонтных заданий
    repair_tasks: Mapped[list["RepairTask"]] = relationship(back_populates="rolling_stock")