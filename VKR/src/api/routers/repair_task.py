from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies import get_db_session
from src.services.repair_tasks import RepairTaskService
from src.schemas.repair_tasks import RepairTaskCreate, RepairTaskResponse, RepairTaskWithStagesResponse

router = APIRouter(prefix="/repair-tasks", tags=["Ремонтные задания"])

@router.post("/", response_model=RepairTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_in: RepairTaskCreate, session: AsyncSession = Depends(get_db_session)):
    """Создание задания на основе регламента"""
    return await RepairTaskService(session).create_task(task_in)

@router.get("/active", response_model=List[RepairTaskResponse])
async def get_active_tasks(session: AsyncSession = Depends(get_db_session)):
    """Получить все активные задачи"""
    return await RepairTaskService(session).get_all_active()

@router.get("/archive", response_model=List[RepairTaskResponse])
async def get_archive_tasks(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_db_session)):
    """Получить все завершенные задания (архив)"""
    return await RepairTaskService(session).get_archived_tasks(skip=skip, limit=limit)

@router.get("/{task_id}/full", response_model=RepairTaskWithStagesResponse)
async def get_task_graph(task_id: int, session: AsyncSession = Depends(get_db_session)):
    """Получить задание со всеми вложенными этапами, бригадами и деталями"""
    return await RepairTaskService(session).get_full_task(task_id)

@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_db_session)):
    """
    Удалить можно только ошибочно созданное задание.
    Активные и завершенные защищены на уровне сервиса.
    """
    await RepairTaskService(session).delete_task(task_id)