from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base import BaseRepository
from src.models.parts_and_materials import PartAndMaterial
from src.models.regulations import Regulation
from src.models.work_brigades import WorkBrigade
from src.schemas.parts_and_materials import PartAndMaterialCreate, PartAndMaterialUpdate
from src.schemas.regulations import RegulationCreate, RegulationUpdate
from src.schemas.work_brigades import WorkBrigadeCreate, WorkBrigadeUpdate

class PartRepository(BaseRepository[PartAndMaterial, PartAndMaterialCreate, PartAndMaterialUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(PartAndMaterial, session)

class RegulationRepository(BaseRepository[Regulation, RegulationCreate, RegulationUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(Regulation, session)

class BrigadeRepository(BaseRepository[WorkBrigade, WorkBrigadeCreate, WorkBrigadeUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(WorkBrigade, session)