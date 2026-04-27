from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import get_db_session
from src.services.catalogs import BrigadeService, PartService, RegulationService
from src.schemas.work_brigades import WorkBrigadeCreate, WorkBrigadeUpdate, WorkBrigadeResponse
from src.schemas.parts_and_materials import PartAndMaterialCreate, PartAndMaterialUpdate, PartAndMaterialResponse
from src.schemas.regulations import RegulationCreate, RegulationUpdate, RegulationResponse

router = APIRouter(prefix="/catalogs", tags=["Справочники"])

# --- БРИГАДЫ ---
@router.get("/brigades", response_model=list[WorkBrigadeResponse])
async def get_brigades(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_db_session)):
    return await BrigadeService(session).get_all(skip, limit)


@router.get("/brigades/{id}", response_model=WorkBrigadeResponse)
async def get_brigade_by_id(id: int, session: AsyncSession = Depends(get_db_session)):
    obj = await BrigadeService(session).repo.get_by_id(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Бригада не найдена")
    return obj


@router.post("/brigades", response_model=WorkBrigadeResponse, status_code=status.HTTP_201_CREATED)
async def create_brigade(data_in: WorkBrigadeCreate, session: AsyncSession = Depends(get_db_session)):
    return await BrigadeService(session).create(data_in)


@router.patch("/brigades/{id}", response_model=WorkBrigadeResponse)
async def update_brigade(id: int, data: WorkBrigadeUpdate, session: AsyncSession = Depends(get_db_session)):
    return await BrigadeService(session).update(id, data)


@router.delete("/brigades/{id}", status_code=204)
async def delete_brigade(id: int, session: AsyncSession = Depends(get_db_session)):
    await BrigadeService(session).delete(id)

# --- ЗАПЧАСТИ ---
@router.get("/parts", response_model=list[PartAndMaterialResponse])
async def get_parts(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_db_session)):
    return await PartService(session).get_all(skip, limit)


@router.get("/parts/{id}", response_model=PartAndMaterialResponse)
async def get_part_by_id(id: int, session: AsyncSession = Depends(get_db_session)):
    obj = await PartService(session).repo.get_by_id(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Запчасть не найдена")
    return obj


@router.post("/parts", response_model=PartAndMaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_part(data_in: PartAndMaterialCreate, session: AsyncSession = Depends(get_db_session)):
    return await PartService(session).create(data_in)


@router.patch("/parts/{id}", response_model=PartAndMaterialResponse)
async def update_part(id: int, data: PartAndMaterialUpdate, session: AsyncSession = Depends(get_db_session)):
    return await PartService(session).update(id, data)


@router.delete("/parts/{id}", status_code=204)
async def delete_part(id: int, session: AsyncSession = Depends(get_db_session)):
    await PartService(session).delete(id)

# --- НОРМАТИВЫ ---
@router.get("/regulations", response_model=list[RegulationResponse])
async def get_regulations(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_db_session)):
    return await RegulationService(session).get_all(skip, limit)


@router.get("/regulations/{id}", response_model=RegulationResponse)
async def get_regulation_by_id(id: int, session: AsyncSession = Depends(get_db_session)):
    obj = await RegulationService(session).repo.get_by_id(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Регламент не найдена")
    return obj


@router.post("/regulations", response_model=RegulationResponse, status_code=status.HTTP_201_CREATED)
async def create_regulation(data_in: RegulationCreate, session: AsyncSession = Depends(get_db_session)):
    return await RegulationService(session).create(data_in)


@router.patch("/regulations/{id}", response_model=RegulationResponse)
async def update_regulation(id: int, data: RegulationUpdate, session: AsyncSession = Depends(get_db_session)):
    return await RegulationService(session).update(id, data)


@router.delete("/regulations/{id}", status_code=204)
async def delete_regulation(id: int, session: AsyncSession = Depends(get_db_session)):
    await RegulationService(session).delete(id)