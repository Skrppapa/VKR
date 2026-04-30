from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import get_db_session
from src.services.repair_stage import RepairStageService
from src.schemas.repair_stages import RepairStageResponse, StageStatusPatch, RepairStageUpdate

router = APIRouter(prefix="/repair-stages", tags=["Этапы ремонта"])

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
    Изменить статус этапа ремонта (Двигатель всего процесса).
    Каскадно управляет временем и статусом родительского задания.
    """
    service = RepairStageService(session)
    return await service.update_stage_status(stage_id, status_data)

@router.patch("/{stage_id}", response_model=RepairStageResponse)
async def update_stage(stage_id: int, data: RepairStageUpdate, session: AsyncSession = Depends(get_db_session)):
    """Обновление текстовых полей этапа (название)."""
    return await RepairStageService(session).update_stage(stage_id, data)