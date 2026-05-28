from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_serializer, Field
from src.models.enums import RepairTypeEnum, TaskStatusEnum
from src.schemas.repair_stages import RepairStageResponse

class RepairTaskBase(BaseModel):
    repair_type: RepairTypeEnum

class RepairTaskCreate(BaseModel):
    rolling_stock_id: int
    repair_type: RepairTypeEnum
    brigade_id: int

class TaskStatusPatch(BaseModel):
    status: TaskStatusEnum

class RepairTaskResponse(RepairTaskBase):
    id: int
    rolling_stock_id: int
    train_series: str
    brigade_id: Optional[int] = None
    master_name_snapshot: Optional[str] = "Не указан"
    status: TaskStatusEnum
    start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    total_paused_seconds: int = 0
    closure_document_path: Optional[str] = None
    inspector_comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('start_date', 'planned_end_date', "actual_end_date", check_fields=False)
    def format_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        if dt:
            return dt.strftime('%d.%m.%Y %H:%M')
        return None

class RejectTaskSchema(BaseModel):
    comment: str = Field(..., min_length=5, description="Причина отклонения работы")

class RepairTaskWithStagesResponse(RepairTaskResponse):
    stages: List[RepairStageResponse] = []