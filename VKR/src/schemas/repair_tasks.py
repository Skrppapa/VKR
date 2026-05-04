from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_serializer
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
    brigade_id: Optional[int] = None
    master_name_snapshot: Optional[str] = "Не указан"  # Для старых записей
    status: TaskStatusEnum
    start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    total_paused_seconds: int = 0

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('start_date', 'planned_end_date', "actual_end_date", check_fields=False)
    def format_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        if dt:
            return dt.strftime('%d.%m.%Y %H:%M')
        return None


# Расширенный ответ (например, когда запрашивают конкретное задание по ID)
class RepairTaskWithStagesResponse(RepairTaskResponse):
    stages: List[RepairStageResponse] = [] # Подтянет вложенные этапы