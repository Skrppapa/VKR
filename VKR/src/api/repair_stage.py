from fastapi import APIRouter
from src.api.dependencies import DBDep
from src.services.repair_stage import RepairStageService
from src.schemas.repair_stages import RepairStageResponse, StageStatusPatch, RepairStageUpdate

router = APIRouter(prefix="/repair-stages", tags=["Этапы ремонта"])

@router.post("/{stage_id}/assign-part/{part_id}")
async def assign_part(db: DBDep, stage_id: int, part_id: int, quantity: int = 1):
    """Списать деталь со склада и назначить на этап."""
    service = RepairStageService(db)
    return await service.add_part_to_repair_stage(stage_id, part_id, quantity)

@router.patch("/{stage_id}/status", response_model=RepairStageResponse)
async def update_stage_status(stage_id: int, status_data: StageStatusPatch, db: DBDep):
    """
    Изменить статус этапа ремонта (Двигатель всего процесса).
    Каскадно управляет временем и статусом родительского задания.
    """
    service = RepairStageService(db)
    return await service.update_stage_status(stage_id, status_data)

@router.patch("/{stage_id}", response_model=RepairStageResponse)
async def update_stage(stage_id: int, data: RepairStageUpdate, db: DBDep):
    """Обновление текстовых полей этапа (название)."""
    service = RepairStageService(db)
    return await service.update_stage(stage_id, data)


