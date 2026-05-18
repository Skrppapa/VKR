from pydantic import BaseModel, field_serializer
from typing import List, Optional
from datetime import datetime

class PlanningItemResponse(BaseModel):
    repair_type: str
    last_repair_date: Optional[datetime]
    next_repair_date: datetime
    days_remaining: int
    is_overdue: bool


    @field_serializer('last_repair_date', 'next_repair_date', check_fields=False)
    def format_dates(self, dt: Optional[datetime], _info) -> Optional[str]:
        if dt:
            return dt.strftime('%d.%m.%Y %H:%M')
        return "Не проводился"

class TrainPlanningResponse(BaseModel):
    inventory_number: str
    series: str
    planning: List[PlanningItemResponse]