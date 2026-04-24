from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import get_db_session
from src.services.repair_stage import RepairStageService
from src.schemas.repair_stages import RepairStageCreate, RepairStageResponse
from src.schemas.repair_stages import StageStatusPatch, RepairStageUpdate

router = APIRouter(prefix="/repair-stages", tags=["Этапы ремонта"])

@router.post("/", response_model=RepairStageResponse, status_code=status.HTTP_201_CREATED)
async def create_stage(stage_in: RepairStageCreate, session: AsyncSession = Depends(get_db_session)):
    return await RepairStageService(session).create_stage(stage_in)

@router.post("/{stage_id}/assign-part/{part_id}")
async def assign_part(stage_id: int, part_id: int, quantity: int = 1, session: AsyncSession = Depends(get_db_session)):
    """Списать деталь со склада и назначить на этап."""
    return await RepairStageService(session).assign_part_to_stage(stage_id, part_id, quantity)

@router.patch("/{stage_id}/status", response_model=RepairStageResponse)
async def update_stage_status(
    stage_id: int,
    status_data: StageStatusPatch,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Изменить статус этапа ремонта.
    Время начала и окончания (start_time / end_time) проставится автоматически.
    """
    service = RepairStageService(session)
    return await service.update_stage_status(stage_id, status_data)

@router.patch("/{stage_id}", response_model=RepairStageResponse)
async def update_stage(stage_id: int, data: RepairStageUpdate, session: AsyncSession = Depends(get_db_session)):
    return await RepairStageService(session).update_stage(stage_id, data)

@router.delete("/{stage_id}", status_code=204)
async def delete_stage(stage_id: int, session: AsyncSession = Depends(get_db_session)):
    await RepairStageService(session).delete_stage(stage_id)