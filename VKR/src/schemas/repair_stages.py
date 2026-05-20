from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from src.models.enums import StageStatusEnum


class PartShortResponse(BaseModel):
    id: int
    nomenclature: str

    model_config = ConfigDict(from_attributes=True)


class StagePartResponse(BaseModel):
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


class RepairStageUpdate(RepairStageBase):
    name: Optional[str] = None
    status: Optional[StageStatusEnum] = None


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

    @field_serializer('start_time', 'end_time', "last_paused_at", check_fields=False)
    def format_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        if dt:
            return dt.strftime('%d.%m.%Y %H:%M')
        return None






