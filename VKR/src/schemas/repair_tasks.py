from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from src.models.enums import RepairTypeEnum, TaskStatusEnum
from src.schemas.repair_stages import RepairStageResponse

class RepairTaskBase(BaseModel):
    repair_type: RepairTypeEnum

class RepairTaskCreate(RepairTaskBase):
    rolling_stock_id: int
    # Статус CREATED и start_date база/модель поставят сами

class RepairTaskUpdate(BaseModel):
    status: Optional[TaskStatusEnum] = None
    planned_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None

# Обычный ответ (например, для списка всех заданий)
class RepairTaskResponse(RepairTaskBase):
    id: int
    rolling_stock_id: int
    status: TaskStatusEnum
    start_date: datetime
    planned_end_date: Optional[datetime]
    actual_end_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# Расширенный ответ (например, когда запрашивают конкретное задание по ID)
class RepairTaskWithStagesResponse(RepairTaskResponse):
    stages: List[RepairStageResponse] = [] # Подтянет вложенные этапы