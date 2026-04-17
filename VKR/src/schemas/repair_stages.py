from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from src.models.enums import StageStatusEnum

# --- Схемы для отображения списанных деталей ---

# 1. Микро-схема для детали (только то, что нужно показать в списке)
class PartShortResponse(BaseModel):
    id: int
    nomenclature: str

    model_config = ConfigDict(from_attributes=True)


# 2. Обновленная схема связи (без поля nomenclature напрямую)
class StagePartResponse(BaseModel):
    # part_id
    quantity_used: int
    part: PartShortResponse  # Pydantic сам зайдет в связь stage_part.part и достанет данные!

    model_config = ConfigDict(from_attributes=True)


# --- Базовые схемы Этапа ---

class RepairStageBase(BaseModel):
    name: str
    status: StageStatusEnum = StageStatusEnum.PENDING


class RepairStageCreate(RepairStageBase):
    repair_task_id: int
    regulation_id: Optional[int] = None


class RepairStageUpdate(BaseModel):
    status: Optional[StageStatusEnum] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# Схема ответа (Чтение этапа)
class RepairStageResponse(RepairStageBase):
    id: int
    repair_task_id: int
    regulation_id: Optional[int]
    start_time: Optional[datetime]
    end_time: Optional[datetime]

    # ВАЖНО: Мы не тянем сюда все детали по умолчанию,
    # чтобы не перегружать обычные списочные запросы.
    model_config = ConfigDict(from_attributes=True)