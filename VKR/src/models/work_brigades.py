from src.database import Base
from src.models.repair_stages import stage_brigade_association
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String


class WorkBrigade(Base):
    """Рабочая бригада"""
    __tablename__ = "work_brigades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    stages: Mapped[list["RepairStage"]] = relationship(secondary=stage_brigade_association, back_populates="brigades")
