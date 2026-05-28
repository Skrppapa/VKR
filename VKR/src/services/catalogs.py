from fastapi import HTTPException, status
from src.models import WorkBrigade, PartAndMaterial
from src.schemas.work_brigades import WorkBrigadeCreate, WorkBrigadeUpdate
from src.schemas.parts_and_materials import PartAndMaterialCreate, PartAndMaterialUpdate
from src.schemas.regulations import RegulationCreate, RegulationUpdate
from src.utils.db_manager import DBManager


class BrigadeService:
    def __init__(self, db: DBManager):
        self.db = db

    async def create(self, data_in: WorkBrigadeCreate):
        obj = await self.db.brigades.create(data_in)
        await self.db.commit()
        return obj

    async def get_all(self, skip: int = 0, limit: int = 100):
        return await self.db.brigades.get_all(skip, limit)

    async def get_brigade_by_id(self, brigade_id: int) -> WorkBrigade:
        brigade = await self.db.brigades.get_by_id(brigade_id)
        if not brigade:
            raise HTTPException(404,"Бригада не найдена")
        return brigade

    async def update(self, obj_id: int, data_in: WorkBrigadeUpdate):
        obj = await self.db.brigades.get_by_id(obj_id)
        if not obj:
            raise HTTPException(404, "Бригада не найдена")
        updated_obj = await self.db.brigades.update(obj, data_in)
        await self.db.commit()
        return updated_obj

    async def delete(self, obj_id: int):
        obj = await self.db.brigades.get_by_id(obj_id)
        if not obj:
            raise HTTPException(404, "Бригада не найдена")
        await self.db.brigades.delete(obj_id)
        await self.db.commit()

class PartService:
    def __init__(self, db: DBManager):
        self.db = db

    async def create(self, data_in: PartAndMaterialCreate):
        obj = await self.db.parts.create(data_in)
        await self.db.commit()
        return obj

    async def get_all(self, skip: int = 0, limit: int = 100):
        return await self.db.parts.get_all(skip, limit)

    async def get_part_by_id(self, part_id: int) -> PartAndMaterial:
        part = await self.db.parts.get_by_id(part_id)
        if not part:
            raise HTTPException(404,"Материал не найден")
        return part

    async def update(self, obj_id: int, data_in: PartAndMaterialUpdate):
        obj = await self.db.parts.get_by_id(obj_id)
        if not obj:
            raise HTTPException(404, "Материал не найден")
        updated_obj = await self.db.parts.update(obj, data_in)
        await self.db.commit()
        return updated_obj

    async def delete(self, obj_id: int):
        obj = await self.db.parts.get_by_id(obj_id)
        if not obj:
            raise HTTPException(404, "Материал не найден")
        await self.db.parts.delete(obj_id)
        await self.db.commit()


class RegulationService:
    def __init__(self, db: DBManager):
        self.db = db

    async def create(self, data_in: RegulationCreate):
        """Создание регламента с этапами"""

        series_exists = await self.db.trains.check_series_exists(data_in.train_series)
        if not series_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Невозможно создать регламент: МВПС серии '{data_in.train_series}' нет в системе."
            )

        existing_reg = await self.db.regulations.get_by_type_and_series(
            repair_type=data_in.repair_type,
            train_series=data_in.train_series
        )

        if existing_reg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Регламент для ремонта '{data_in.repair_type.value}' серии '{data_in.train_series}' уже существует."
            )

        new_reg = await self.db.regulations.create(data_in)
        reg_id = new_reg.id
        await self.db.commit()
        return await self.db.regulations.get_by_id(reg_id)

    async def get_all(self, skip: int = 0, limit: int = 100):
        return await self.db.regulations.get_all(skip, limit)

    async def get_regulation_by_id(self, regulation_id: int):
        regulation = await self.db.regulations.get_by_id(regulation_id)
        if not regulation:
            raise HTTPException(
                404, "Регламент не найден.")
        return regulation

    async def update(self, obj_id: int, data_in: RegulationUpdate):
        obj = await self.db.regulations.get_by_id(obj_id)
        if not obj:
            raise HTTPException(404, "Норматив не найден")
        updated_obj = await self.db.regulations.update(obj, data_in)
        await self.db.commit()
        return updated_obj

    async def delete(self, obj_id: int):
        obj = await self.db.regulations.get_by_id(obj_id)
        if not obj:
            raise HTTPException(404, "Регламент не найден")
        await self.db.regulations.delete(obj_id)
        await self.db.commit()
