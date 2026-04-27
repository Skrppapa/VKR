from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from src.models.enums import StageStatusEnum

# Микро-схема для детали
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

    model_config = ConfigDict(from_attributes=True)


