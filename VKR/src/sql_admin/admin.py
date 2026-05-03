from datetime import datetime, timezone
from urllib.request import Request
from sqladmin import ModelView, BaseView, expose
from src.utils.db_manager import DBManager
import json
from sqlalchemy import select
from src.database import async_session_maker
from src.services.planning import PlanningService
from src.models import (
    RollingStock, Regulation, PartAndMaterial,
    WorkBrigade, RepairTask, RepairStage
)
from fastapi import Request
from sqlalchemy.orm import selectinload
from src.models.enums import TaskStatusEnum

class RollingStockAdmin(ModelView, model=RollingStock):
    column_list = [RollingStock.id, RollingStock.inventory_number, RollingStock.series, RollingStock.manufacture_date]
    name = "Поезд (МВПС)"
    name_plural = "Поезда (МВПС)"
    icon = "fa-solid fa-train"
    column_searchable_list = [RollingStock.inventory_number, RollingStock.series]

class RegulationAdmin(ModelView, model=Regulation):
    column_list = [Regulation.id, Regulation.repair_type, Regulation.train_series, Regulation.standard_hours, Regulation.frequency_days]
    name = "Регламент"
    name_plural = "Регламенты"
    icon = "fa-solid fa-book"

class PartAndMaterialAdmin(ModelView, model=PartAndMaterial):
    column_list = [PartAndMaterial.id, PartAndMaterial.nomenclature, PartAndMaterial.stock_quantity]
    name = "Запчасть"
    name_plural = "Склад запчастей"
    icon = "fa-solid fa-box"
    column_searchable_list = [PartAndMaterial.nomenclature]

class WorkBrigadeAdmin(ModelView, model=WorkBrigade):
    column_list = [WorkBrigade.id, WorkBrigade.name]
    name = "Бригада"
    name_plural = "Рабочие бригады"
    icon = "fa-solid fa-users"

class RepairTaskAdmin(ModelView, model=RepairTask):
    column_list = [RepairTask.id, RepairTask.rolling_stock_id, RepairTask.repair_type, RepairTask.status, RepairTask.planned_end_date]
    name = "Задание"
    name_plural = "Ремонтные задания"
    icon = "fa-solid fa-clipboard-list"
    # Запрещаем создавать задания из админки (это делает только наше API с автогенерацией этапов)
    can_create = False
    can_edit = False
    can_delete = True

class RepairStageAdmin(ModelView, model=RepairStage):
    column_list = [RepairStage.id, RepairStage.repair_task_id, RepairStage.name, RepairStage.status]
    name = "Этап ремонта"
    name_plural = "Этапы ремонта"
    icon = "fa-solid fa-bars-progress"
    can_create = False
    can_edit = False



class DashboardView(BaseView):
    name = "Дашборд"
    icon = "fa-solid fa-chart-pie"

    @expose("/dashboard", methods=["GET"])
    async def dashboard(self, request: Request):
        planning_data = []
        chart_labels = []
        chart_values = []

        # Переменные для блока "Контроль"
        in_progress_count = 0
        paused_count = 0
        active_tasks_data = []

        # 1. Открываем транзакцию через наш менеджер
        async with DBManager(session_factory=async_session_maker) as db:
            service = PlanningService(db)

            # --- БЛОК ПЛАНИРОВАНИЯ ---
            trains_query = select(RollingStock)
            # 3. Обращаемся к сессии внутри менеджера
            trains = (await db.session.execute(trains_query)).scalars().all()
            total_trains = len(trains)

            for train in trains:
                plan_info = await service.get_train_planning_status(train.id)
                if plan_info and plan_info["planning"]:
                    planning_data.append(plan_info)
                    min_days = min(p["days_remaining"] for p in plan_info["planning"])
                    chart_labels.append(f"{train.series} ({train.inventory_number})")
                    chart_values.append(min_days)

            # --- БЛОК КОНТРОЛЯ ---
            active_tasks_query = (
                select(RepairTask)
                .where(RepairTask.status != TaskStatusEnum.COMPLETED)
                .options(selectinload(RepairTask.rolling_stock))
            )
            # 3. Снова используем db.session.execute
            active_tasks = (await db.session.execute(active_tasks_query)).scalars().all()

            now = datetime.now(timezone.utc)

            for task in active_tasks:
                if task.status == TaskStatusEnum.IN_PROGRESS:
                    in_progress_count += 1
                elif task.status in [TaskStatusEnum.PAUSED, TaskStatusEnum.WAITING_PARTS]:
                    paused_count += 1

                # Проверяем, просрочена ли текущая задача
                is_task_overdue = False
                if task.planned_end_date and task.planned_end_date < now:
                    is_task_overdue = True

                active_tasks_data.append({
                    "task": task,
                    "is_overdue": is_task_overdue
                })

        chart_data_json = json.dumps({
            "labels": chart_labels,
            "values": chart_values
        })

        return await self.templates.TemplateResponse(
            request,
            "dashboard.html",
            context={
                "planning_data": planning_data,
                "chart_data": chart_data_json,
                "total_trains": total_trains,
                "in_progress_count": in_progress_count,
                "paused_count": paused_count,
                "active_tasks": active_tasks_data
            }
        )