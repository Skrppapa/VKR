from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class RollingStockBase(BaseModel):
    inventory_number: str = Field(..., max_length=50, description="Инвентарный № поезда")
    series: str = Field(..., max_length=50, description="Серийный № поезда")
    manufacture_date: date


class RollingStockCreate(RollingStockBase):
    pass


class RollingStockUpdate(BaseModel):
    inventory_number: Optional[str] = Field(None, max_length=50, description="Инвентарный № поезда")
    series: Optional[str] = Field(None, max_length=50, description="Серийный № поезда")
    manufacture_date: Optional[date] = None

class RollingStockResponse(RollingStockBase):
    id: int

    model_config = ConfigDict(from_attributes=True)