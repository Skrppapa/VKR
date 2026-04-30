from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import WorkBrigade, PartAndMaterial, Regulation
from src.repositories.catalogs import BrigadeRepository, PartRepository, RegulationRepository
from src.repositories.rolling_stock import RollingStockRepository
from src.schemas.work_brigades import WorkBrigadeCreate, WorkBrigadeUpdate
from src.schemas.parts_and_materials import PartAndMaterialCreate, PartAndMaterialUpdate
from src.schemas.regulations import RegulationCreate, RegulationUpdate


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

    async def get_brigade_by_id(self, brigade_id: int) -> WorkBrigade:
        brigade = await self.repo.get_by_id(brigade_id)
        if not brigade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бригада не найдена"
            )
        return brigade

    async def update(self, obj_id: int, data_in: WorkBrigadeUpdate):
        obj = await self.repo.get_by_id(obj_id)
        if not obj:
            raise HTTPException(404, "Бригада не найдена")
        updated_obj = await self.repo.update(obj, data_in)
        await self.session.commit()
        return updated_obj

    async def delete(self, obj_id: int):
        obj = await self.repo.get_by_id(obj_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бригада не найдена")
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

    async def get_part_by_id(self, part_id: int) -> PartAndMaterial:
        part = await self.repo.get_by_id(part_id)
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Материал не найден"
            )
        return part

    async def update(self, obj_id: int, data_in: PartAndMaterialUpdate):
        obj = await self.repo.get_by_id(obj_id)
        if not obj: raise HTTPException(404, "Материал не найден")
        updated_obj = await self.repo.update(obj, data_in)
        await self.session.commit()
        return updated_obj

    async def delete(self, obj_id: int):
        obj = await self.repo.get_by_id(obj_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Материал не найден")
        await self.repo.delete(obj_id)
        await self.session.commit()


class RegulationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RegulationRepository(session)
        self.rolling_stock_repo = RollingStockRepository(session)

    async def create(self, data_in: RegulationCreate):
        """Создание регламента с этапами"""

        # Проверяем существует ли в бд модель поезда для которой создаем регламент
        series_exists = await self.rolling_stock_repo.check_series_exists(data_in.train_series)
        if not series_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Невозможно создать регламент: поездов серии '{data_in.train_series}' нет в системе."
            )

        # Проверяем наличие дубликатов регламента
        existing_reg = await self.repo.get_by_type_and_series(
            repair_type=data_in.repair_type,
            train_series=data_in.train_series
        )

        if existing_reg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Регламент для ремонта '{data_in.repair_type.value}' серии '{data_in.train_series}' уже существует."
            )

        # Создание
        new_reg = await self.repo.create(data_in)
        reg_id = new_reg.id
        await self.session.commit()
        return await self.repo.get_by_id(reg_id)

    async def get_all(self, skip: int = 0, limit: int = 100):
        return await self.repo.get_all(skip, limit)

    async def get_regulation_by_id(self, regulation_id: int) -> Regulation:
        regulation = await self.repo.get_by_id(regulation_id)
        if not regulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Регламент не найден."
            )
        return regulation

    async def update(self, obj_id: int, data_in: RegulationUpdate):
        obj = await self.repo.get_by_id(obj_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Норматив не найден")
        updated_obj = await self.repo.update(obj, data_in)
        await self.session.commit()
        return updated_obj

    async def delete(self, obj_id: int):
        obj = await self.repo.get_by_id(obj_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Регламент не найден")
        await self.repo.delete(obj_id)
        await self.session.commit()
