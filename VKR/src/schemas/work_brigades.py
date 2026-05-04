from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Базовая схема - содержит только то, что гарантированно есть у всех записей (и старых, и новых)
class WorkBrigadeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Уникальное название бригады")

# Схема создания - здесь ФИО и табельный номер СТРОГО обязательны
class WorkBrigadeCreate(WorkBrigadeBase):
    master_name: str = Field(..., min_length=2, max_length=150, description="ФИО руководителя")
    master_id_number: str = Field(..., min_length=7, max_length=7, description="Табельный номер (7 цифр)")

    @field_validator("master_id_number")
    @classmethod
    def validate_master_id(cls, v: str):
        if not v.isdigit():
            raise ValueError("Табельный номер должен состоять только из цифр")
        return v

# Схема обновления - все поля опциональны (для частичного PATCH-обновления)
class WorkBrigadeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    master_name: Optional[str] = Field(None, min_length=2, max_length=150)
    master_id_number: Optional[str] = Field(None, min_length=7, max_length=7)

    @field_validator("master_id_number")
    @classmethod
    def validate_master_id(cls, v: Optional[str]):
        if v is not None and not v.isdigit():
            raise ValueError("Табельный номер должен состоять только из цифр")
        return v

# Схема ответа - поля мастера помечены как Optional, чтобы старые записи из БД (где NULL) не роняли приложение
class WorkBrigadeResponse(WorkBrigadeBase):
    id: int
    master_name: Optional[str] = None
    master_id_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)