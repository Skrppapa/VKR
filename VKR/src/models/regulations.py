from src.database import Base
from src.models.enums import RepairTypeEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, Integer


class Regulation(Base):
    """Нормативы"""
    __tablename__ = "regulations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    repair_type: Mapped[RepairTypeEnum] = mapped_column(Enum(RepairTypeEnum), unique=True)
    standard_hours: Mapped[int] = mapped_column(Integer)  # Норма времени в часах на данный вид ремонта

    stages: Mapped[list["RepairStage"]] = relationship(back_populates="regulation")