from src.database import Base, int_pk
from src.models.repair_stages import stage_brigade_association
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String


class WorkBrigade(Base):
    """Рабочая бригада"""
    __tablename__ = "work_brigades"

    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(100), unique=True)
    master_name: Mapped[str] = mapped_column(String(150), nullable=True)
    master_id_number: Mapped[str] = mapped_column(String(7), nullable=True)

    stages: Mapped[list["RepairStage"]] = relationship(secondary=stage_brigade_association, back_populates="brigades")
    repair_tasks: Mapped[list["RepairTask"]] = relationship(back_populates="brigade")

    def __str__(self):
        return self.name