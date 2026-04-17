from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from src.models.enums import RepairTypeEnum

class RegulationBase(BaseModel):
    repair_type: RepairTypeEnum = Field(..., description="Вид ремонта (ТО-1, ТР-2 и т.д.)")
    standard_hours: int = Field(..., gt=0, description="Норма времени в часах")

class RegulationCreate(RegulationBase):
    pass

class RegulationUpdate(BaseModel):
    repair_type: Optional[RepairTypeEnum] = None
    standard_hours: Optional[int] = Field(None, gt=0)

class RegulationResponse(RegulationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)