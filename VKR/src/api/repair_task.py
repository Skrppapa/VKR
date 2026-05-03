from fastapi import APIRouter, status
from typing import List
from src.api.dependencies import DBDep
from src.services.repair_tasks import RepairTaskService
from src.schemas.repair_tasks import RepairTaskCreate, RepairTaskResponse, RepairTaskWithStagesResponse


router = APIRouter(prefix="/repair-tasks", tags=["Ремонтные задания"])

@router.post("/", response_model=RepairTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_in: RepairTaskCreate, db: DBDep):
    """Создание задания на основе регламента"""
    service = RepairTaskService(db)
    return await service.create_task(task_in)

@router.get("/active", response_model=List[RepairTaskResponse])
async def get_active_tasks(db: DBDep):
    """Получить все активные задачи"""
    service = RepairTaskService(db)
    return await service.get_all_active()

@router.get("/archive", response_model=List[RepairTaskResponse])
async def get_archive_tasks(db: DBDep, skip: int = 0, limit: int = 100):
    """Получить все завершенные задания (архив)"""
    service = RepairTaskService(db)
    return await service.get_archived_tasks(skip=skip, limit=limit)

@router.get("/{task_id}/full", response_model=RepairTaskWithStagesResponse)
async def get_task_graph(task_id: int, db: DBDep):
    """Получить задание со всеми вложенными этапами, бригадами и деталями"""
    service = RepairTaskService(db)
    return await service.get_full_task(task_id)

@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, db: DBDep):
    """
    Удалить можно только ошибочно созданное задание.
    Активные и завершенные защищены на уровне сервиса.
    """
    service = RepairTaskService(db)
    await service.delete_task(task_id)