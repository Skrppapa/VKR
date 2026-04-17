from src.database import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer


class StagePart(Base):
    """Модель для связи Этап - Запчасть с указанием количества"""
    __tablename__ = "stage_parts"

    # Составной первичный ключ из двух внешних ключей
    stage_id: Mapped[int] = mapped_column(ForeignKey("repair_stages.id"), primary_key=True)
    part_id: Mapped[int] = mapped_column(ForeignKey("parts_and_materials.id"), primary_key=True)

    # Полезная нагрузка связи!
    quantity_used: Mapped[int] = mapped_column(Integer, default=1)

    # Связи к родительским таблицам
    stage: Mapped["RepairStage"] = relationship(back_populates="part_associations")
    part: Mapped["PartAndMaterial"] = relationship(back_populates="stage_associations")