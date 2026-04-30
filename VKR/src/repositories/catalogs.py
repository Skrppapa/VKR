from sqlalchemy.ext.asyncio import AsyncSession
from src.models import RegulationStageTemplate
from src.repositories.base import BaseRepository
from src.models.parts_and_materials import PartAndMaterial
from src.models.regulations import Regulation
from src.models.work_brigades import WorkBrigade
from src.schemas.parts_and_materials import PartAndMaterialCreate, PartAndMaterialUpdate
from src.schemas.regulations import RegulationCreate, RegulationUpdate
from src.schemas.work_brigades import WorkBrigadeCreate, WorkBrigadeUpdate
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List

class PartRepository(BaseRepository[PartAndMaterial, PartAndMaterialCreate, PartAndMaterialUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(PartAndMaterial, session)


class BrigadeRepository(BaseRepository[WorkBrigade, WorkBrigadeCreate, WorkBrigadeUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(WorkBrigade, session)


class RegulationRepository(BaseRepository[Regulation, RegulationCreate, RegulationUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(Regulation, session)

    async def get_by_type_and_series(self, repair_type: str, train_series: str) -> Optional[Regulation]:
        """Метод для проверки дубликатов."""
        query = select(self.model).where(
            self.model.repair_type == repair_type,
            self.model.train_series == train_series
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, obj_in: RegulationCreate) -> Regulation:
        """Переопределенный create для работы с вложенными шаблонами"""
        data_dict = obj_in.model_dump()
        templates_data = data_dict.pop("templates", [])

        # Создаем родительский объект
        new_reg = self.model(**data_dict)

        # Создаем и привязываем дочерние объекты
        for t_data in templates_data:
            new_reg.templates.append(RegulationStageTemplate(**t_data))

        self.session.add(new_reg)
        await self.session.flush()
        return new_reg

    async def get_by_id(self, obj_id: int) -> Optional[Regulation]:
        query = (
            select(self.model)
            .where(self.model.id == obj_id)
            .options(selectinload(self.model.templates))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Regulation]:
        query = (
            select(self.model)
            .options(selectinload(self.model.templates))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
