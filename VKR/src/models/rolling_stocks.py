from src.database import Base, int_pk
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Date
from datetime import date


class RollingStock(Base):
    """Подвижной состав (МВПС)"""
    __tablename__ = "rolling_stocks"

    id: Mapped[int_pk]
    inventory_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    series: Mapped[str] = mapped_column(String(50))
    manufacture_date: Mapped[date] = mapped_column(Date)

    repair_tasks: Mapped[list["RepairTask"]] = relationship(back_populates="rolling_stock")

    def __str__(self):
        return f"{self.series} (№{self.inventory_number})"