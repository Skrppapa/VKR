from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from src.models.enums import StageStatusEnum

# Схема для детали
class PartShortResponse(BaseModel):
    id: int
    nomenclature: str

    model_config = ConfigDict(from_attributes=True)


class StagePartResponse(BaseModel):
    # part_id
    quantity_used: int
    part: PartShortResponse

    model_config = ConfigDict(from_attributes=True)


class RepairStageBase(BaseModel):
    name: str
    status: StageStatusEnum = StageStatusEnum.PENDING


class RepairStageCreate(RepairStageBase):
    repair_task_id: int
    regulation_id: Optional[int] = None


class StageStatusPatch(BaseModel):
    status: StageStatusEnum
    pause_reason: Optional[str] = Field(None, max_length=500,
                                        description="Причина паузы. Обязательна, если статус PAUSED")


class RepairStageUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[StageStatusEnum] = None
    regulation_id: Optional[int] = None


# Схема ответа (Чтение этапа)
class RepairStageResponse(RepairStageBase):
    id: int
    repair_task_id: int
    regulation_id: Optional[int]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    last_paused_at: Optional[datetime] = None
    total_paused_seconds: int = 0
    pause_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)






