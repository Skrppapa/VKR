from datetime import date
from pydantic import BaseModel, ConfigDict, Field

class RollingStockBase(BaseModel):
    inventory_number: str = Field(..., max_length=50, description="Инвентарный № поезда")
    series: str = Field(..., max_length=50, description="Серийный № поезда")
    manufacture_date: date

class RollingStockCreate(RollingStockBase):
    pass # Те же поля что и в БД

class RollingStockResponse(RollingStockBase):
    id: int


    model_config = ConfigDict(from_attributes=True)