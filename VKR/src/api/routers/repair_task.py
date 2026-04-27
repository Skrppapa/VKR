from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies import get_db_session
from src.services.repair_tasks import RepairTaskService
from src.schemas.repair_tasks import RepairTaskCreate, RepairTaskResponse, RepairTaskWithStagesResponse
from src.schemas.repair_tasks import TaskStatusPatch

router = APIRouter(prefix="/repair-tasks", tags=["Ремонтные задания"])

@router.post("/", response_model=RepairTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_in: RepairTaskCreate, session: AsyncSession = Depends(get_db_session)):
    return await RepairTaskService(session).create_task(task_in)

@router.get("/active", response_model=List[RepairTaskResponse])
async def get_active_tasks(session: AsyncSession = Depends(get_db_session)):
    return await RepairTaskService(session).get_all_active()

@router.get("/{task_id}/full", response_model=RepairTaskWithStagesResponse)
async def get_task_graph(task_id: int, session: AsyncSession = Depends(get_db_session)):
    """Получить задание со всеми вложенными этапами, бригадами и деталями."""
    return await RepairTaskService(session).get_full_task(task_id)

@router.patch("/{task_id}/status", response_model=RepairTaskResponse)
async def update_task_status(
    task_id: int,
    status_data: TaskStatusPatch,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Изменить статус ремонтного задания.
    Нельзя установить статус 'Завершено', если есть незаконченные этапы.
    """
    service = RepairTaskService(session)
    return await service.update_task_status(task_id, status_data)

@router.patch("/{task_id}", response_model=RepairTaskResponse)
async def update_task(task_id: int, data: TaskStatusPatch, session: AsyncSession = Depends(get_db_session)):
    return await RepairTaskService(session).update_task(task_id, data)

@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_db_session)):
    await RepairTaskService(session).delete_task(task_id)