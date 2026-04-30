from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkBrigadeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Уникальное название бригады")

class WorkBrigadeCreate(WorkBrigadeBase):
    pass

class WorkBrigadeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)

class WorkBrigadeResponse(WorkBrigadeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)