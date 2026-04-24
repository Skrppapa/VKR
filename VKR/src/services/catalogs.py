from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.catalogs import BrigadeRepository, PartRepository, RegulationRepository
from src.schemas.work_brigades import WorkBrigadeCreate
from src.schemas.parts_and_materials import PartAndMaterialCreate
from src.schemas.regulations import RegulationCreate
from fastapi import HTTPException, status
from src.schemas.work_brigades import WorkBrigadeUpdate
from src.schemas.parts_and_materials import PartAndMaterialUpdate
from src.schemas.regulations import RegulationUpdate


class BrigadeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BrigadeRepository(session)

    async def create(self, data_in: WorkBrigadeCreate):
        obj = await self.repo.create(data_in)
        await self.session.commit()
        return obj

    async def get_all(self, skip: int = 0, limit: int = 100):
        return await self.repo.get_all(skip, limit)

    async def update(self, obj_id: int, data_in: WorkBrigadeUpdate):
        obj = await self.repo.get_by_id(obj_id)
        if not obj: raise HTTPException(404, "Бригада не найдена")
        updated_obj = await self.repo.update(obj, data_in)
        await self.session.commit()
        return updated_obj

    async def delete(self, obj_id: int):
        await self.repo.delete(obj_id)
        await self.session.commit()

class PartService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PartRepository(session)

    async def create(self, data_in: PartAndMaterialCreate):
        obj = await self.repo.create(data_in)
        await self.session.commit()
        return obj

    async def get_all(self, skip: int = 0, limit: int = 100):
        return await self.repo.get_all(skip, limit)

    async def update(self, obj_id: int, data_in: PartAndMaterialUpdate):
        obj = await self.repo.get_by_id(obj_id)
        if not obj: raise HTTPException(404, "Запчасть не найдена")
        updated_obj = await self.repo.update(obj, data_in)
        await self.session.commit()
        return updated_obj

    async def delete(self, obj_id: int):
        await self.repo.delete(obj_id)
        await self.session.commit()

class RegulationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RegulationRepository(session)

    async def create(self, data_in: RegulationCreate):
        obj = await self.repo.create(data_in)
        await self.session.commit()
        return obj

    async def get_all(self, skip: int = 0, limit: int = 100):
        return await self.repo.get_all(skip, limit)

    async def update(self, obj_id: int, data_in: RegulationUpdate):
        obj = await self.repo.get_by_id(obj_id)
        if not obj: raise HTTPException(404, "Норматив не найден")
        updated_obj = await self.repo.update(obj, data_in)
        await self.session.commit()
        return updated_obj

    async def delete(self, obj_id: int):
        await self.repo.delete(obj_id)
        await self.session.commit()
