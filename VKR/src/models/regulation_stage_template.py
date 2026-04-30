from src.database import Base, int_pk
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey

class RegulationStageTemplate(Base):
    __tablename__ = "regulation_stage_templates"

    id: Mapped[int_pk]
    regulation_id: Mapped[int] = mapped_column(ForeignKey("regulations.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False) # Порядок выполнения

    regulation: Mapped["Regulation"] = relationship(back_populates="templates")