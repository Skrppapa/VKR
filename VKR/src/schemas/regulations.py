from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.models.enums import RepairTypeEnum

# Шаблоны
class RegulationTemplateBase(BaseModel):
    name: str = Field(..., description="Название этапа (например, Диагностика)")
    order_number: int = Field(..., gt=0, description="Порядковый номер выполнения")


class RegulationTemplateCreate(RegulationTemplateBase):
    pass


class RegulationTemplateResponse(RegulationTemplateBase):
    id: int
    regulation_id: int
    model_config = ConfigDict(from_attributes=True)


# Регламенты
class RegulationBase(BaseModel):
    repair_type: RepairTypeEnum = Field(..., description="Вид ремонта")
    train_series: str = Field(..., max_length=50, description="Серия поезда")
    standard_hours: int = Field(..., gt=0, description="Норма времени в часах")


class RegulationCreate(RegulationBase):
    templates: List[RegulationTemplateCreate] = Field(..., min_length=1, description="Список этапов по порядку")

    @field_validator("templates")
    @classmethod
    def validate_order_numbers(cls, templates: List[RegulationTemplateCreate]):
        orders = sorted([t.order_number for t in templates])  # Собираем все переданные order_number и сортируем
        expected_orders = list(range(1, len(templates) + 1))  # Генерируем последовательность от 1 до N (где N - количество этапов)

        if orders != expected_orders:
            raise ValueError(
                f"Порядковые номера этапов (order_number) должны идти строго по порядку без дубликатов и пропусков, "
                f"начиная с 1. Ожидалось: {expected_orders}, получено: {orders}."
            )
        return templates


class RegulationUpdate(BaseModel):
    repair_type: Optional[RepairTypeEnum] = None
    train_series: Optional[str] = None
    standard_hours: Optional[int] = Field(None, gt=0)


class RegulationResponse(RegulationBase):
    id: int
    templates: List[RegulationTemplateResponse] = []

    model_config = ConfigDict(from_attributes=True)