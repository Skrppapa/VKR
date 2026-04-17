from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class PartAndMaterialBase(BaseModel):
    nomenclature: str = Field(..., min_length=2, max_length=150, description="Номенклатурное название детали")
    stock_quantity: int = Field(default=0, ge=0, description="Количество на складе")

class PartAndMaterialCreate(PartAndMaterialBase):
    pass

class PartAndMaterialUpdate(BaseModel):
    nomenclature: Optional[str] = Field(None, min_length=2, max_length=150)
    stock_quantity: Optional[int] = Field(None, ge=0)

class PartAndMaterialResponse(PartAndMaterialBase):
    id: int

    model_config = ConfigDict(from_attributes=True)