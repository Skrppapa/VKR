from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from src.database import Base, int_pk

class User(Base):
    __tablename__ = "users"

    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="admin", server_default="admin")