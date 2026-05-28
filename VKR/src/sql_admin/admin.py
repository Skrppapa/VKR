from datetime import datetime, timezone
from typing import Any
from urllib.request import Request
from pydantic import ValidationError
from sqladmin import ModelView, BaseView, expose
from src.schemas.rolling_stocks import RollingStockUpdate, RollingStockCreate
from src.services.rolling_stock import RollingStockService
from src.utils.db_manager import DBManager
import json
from src.database import async_session_maker
from src.services.planning import PlanningService
from src.models import (RollingStock, Regulation, PartAndMaterial, WorkBrigade, RepairTask, RepairStage)
from fastapi import Request, HTTPException, status
from src.models.enums import TaskStatusEnum
from fastapi.responses import RedirectResponse
from src.schemas.repair_tasks import RepairTaskCreate
from src.services.repair_tasks import RepairTaskService
from src.models.enums import RepairTypeEnum
from src.schemas.regulations import RegulationCreate, RegulationTemplateCreate
from src.services.catalogs import RegulationService
from src.services.catalogs import BrigadeService
from src.schemas.work_brigades import WorkBrigadeCreate, WorkBrigadeUpdate
from markupsafe import Markup
from src.models.users import User
from src.security import get_password_hash
from wtforms.fields import SelectField


class BaseModelView(ModelView):
    list_template = "custom_list.html"
    create_template = "custom_create.html"
    edit_template = "custom_edit.html"
    details_template = "custom_details.html"

    can_export = False


class RollingStockAdmin(BaseModelView, model=RollingStock):

    _shared_columns = [
        RollingStock.id,
        RollingStock.inventory_number,
        RollingStock.series,
        RollingStock.manufacture_date
    ]

    column_labels = {
        "id": "ID",
        "inventory_number": "Инвентарный номер",
        "series": "Серия МВПС",
        "manufacture_date": "Дата выпуска"
    }

    column_list = _shared_columns
    column_details_list = _shared_columns

    column_formatters = {
        RollingStock.inventory_number: lambda m, a: Markup(
            f'<a href="/admin/dashboard/train/{m.id}" class="fw-bold text-decoration-none">{m.inventory_number}</a>'
        )
    }

    name = "Поезд (МВПС)"
    name_plural = "Поезда (МВПС)"
    icon = "fa-solid fa-train"
    column_searchable_list = [RollingStock.inventory_number, RollingStock.series]
    form_excluded_columns = ["repair_tasks"]

    async def insert_model(self, request: Request, data: dict) -> Any:
        """Создание МВПС через сервис"""
        async with DBManager(session_factory=async_session_maker) as db:
            service = RollingStockService(db)
            try:
                create_schema = RollingStockCreate(**data)
                return await service.create_train(create_schema)

            except ValidationError as e:
                error_detail = e.errors()[0]['msg']
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ошибка валидации полей: {error_detail}"
                )
            except HTTPException as e:
                raise HTTPException(
                    status_code=e.status_code,
                    detail=e.detail
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Непредвиденная ошибка при создании: {str(e)}"
                )

    async def update_model(self, request: Request, data: dict, model: Any) -> Any:
        """Редактирование МВПС через сервис"""
        async with DBManager(session_factory=async_session_maker) as db:
            service = RollingStockService(db)
            try:
                update_schema = RollingStockUpdate(**data)
                return await service.update_train(model.id, update_schema)

            except ValidationError as e:
                error_detail = e.errors()[0]['msg']
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ошибка валидации изменений: {error_detail}"
                )
            except HTTPException as e:
                raise HTTPException(
                    status_code=e.status_code,
                    detail=e.detail
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Непредвиденная ошибка при обновлении: {str(e)}"
                )


class RegulationAdmin(BaseModelView, model=Regulation):

    _shared_columns = [
        Regulation.id,
        Regulation.repair_type,
        Regulation.train_series,
        Regulation.standard_hours,
        Regulation.frequency_days
    ]

    column_labels = {
        "id": "ID",
        "repair_type": "Вид ремонта",
        "train_series": "Серия поезда",
        "standard_hours": "Норма времени (ч)",
        "frequency_days": "Периодичность (дни)"
    }

    column_list = _shared_columns
    column_details_list = _shared_columns

    name = "Регламент"
    name_plural = "Регламенты"
    icon = "fa-solid fa-book"
    can_create = False
    list_template = "admin_regulation_list.html"
    column_searchable_list = [Regulation.train_series]
    form_excluded_columns = ["stages", "templates"]


class CreateRegulationAdminView(BaseView):
    name = "Создать регламент"
    icon = "fa-solid fa-file-signature"

    def is_visible(self, request: Request) -> bool:
        return False

    @expose("/create-regulation", methods=["GET"])
    async def create_regulation_page(self, request: Request):
        async with DBManager(session_factory=async_session_maker) as db:

            train_series = await db.trains.get_unique_series()

            repair_types = [rt.value for rt in RepairTypeEnum]

            return await self.templates.TemplateResponse(
                request,
                "admin_create_regulation.html",
                context={
                    "request": request,
                    "train_series": train_series,
                    "repair_types": repair_types,
                    "error": request.query_params.get("error")
                }
            )

    @expose("/create-regulation", methods=["POST"])
    async def create_regulation_action(self, request: Request):
        form = await request.form()

        try:
            templates = []

            template_keys = [k for k in form.keys() if k.startswith("template_name_")]
            template_keys.sort(key=lambda x: int(x.split("_")[-1]))

            for i, key in enumerate(template_keys, start=1):
                name = form.get(key)
                if name and name.strip():
                    templates.append(
                        RegulationTemplateCreate(name=name.strip(), order_number=i)
                    )

            if not templates:
                raise ValueError("Необходимо добавить хотя бы один этап ремонта.")

            reg_in = RegulationCreate(
                repair_type=form.get("repair_type"),
                train_series=form.get("train_series"),
                standard_hours=int(form.get("standard_hours")),
                frequency_days=int(form.get("frequency_days", 0)),
                templates=templates
            )

            async with DBManager(session_factory=async_session_maker) as db:
                service = RegulationService(db)
                await service.create(reg_in)

            return RedirectResponse(url="/admin/dashboard", status_code=303)

        except Exception as e:
            error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
            return RedirectResponse(url=f"/admin/create-regulation?error={error_msg}", status_code=303)

class PartAndMaterialAdmin(BaseModelView, model=PartAndMaterial):

    _shared_columns = [
        PartAndMaterial.id,
        PartAndMaterial.nomenclature,
        PartAndMaterial.stock_quantity
    ]

    column_labels = {
        "id": "ID",
        "nomenclature": "Номенклатура",
        "stock_quantity": "Остаток на складе"
    }

    column_list = _shared_columns
    column_details_list = _shared_columns

    name = "Запчасть"
    name_plural = "Склад запчастей"
    icon = "fa-solid fa-box"
    column_searchable_list = [PartAndMaterial.nomenclature]
    form_excluded_columns = ["stage_associations"]


class WorkBrigadeAdmin(BaseModelView, model=WorkBrigade):

    _shared_columns = [
        WorkBrigade.id,
        WorkBrigade.name,
        WorkBrigade.master_name,
        WorkBrigade.master_id_number
    ]

    column_labels = {
        "id": "ID",
        "name": "Название бригады",
        "master_name": "ФИО Мастера",
        "master_id_number": "Табельный номер"
    }

    column_list = _shared_columns
    column_details_list = _shared_columns

    name = "Бригаду"
    name_plural = "Рабочие бригады"
    icon = "fa-solid fa-users"
    column_searchable_list = [WorkBrigade.name, WorkBrigade.master_name]
    form_excluded_columns = [WorkBrigade.stages, WorkBrigade.repair_tasks]

    async def insert_model(self, request: Request, data: dict) -> Any:
        """Создание бригады через сервис"""
        async with DBManager(session_factory=async_session_maker) as db:
            service = BrigadeService(db)
            try:
                create_schema = WorkBrigadeCreate(**data)
                return await service.create(create_schema)

            except (ValidationError, ValueError, HTTPException) as e:
                error_detail = e.errors()[0]['msg'] if hasattr(e, 'errors') else str(e)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ошибка валидации: {error_detail}"
                )

    async def update_model(self, request: Request, data: dict, model: Any) -> Any:
        """Изменение бригады через сервис"""
        async with DBManager(session_factory=async_session_maker) as db:
            service = BrigadeService(db)
            try:
                update_schema = WorkBrigadeUpdate(**data)

                return await service.update(model.id, update_schema)

            except (ValidationError, ValueError, HTTPException) as e:
                error_detail = e.errors()[0]['msg'] if hasattr(e, 'errors') else str(e)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ошибка изменения: {error_detail}"
                )


TASK_STATUS_TRANSLATE = {
    "CREATED": "Создано",
    "IN_PROGRESS": "В работе",
    "PAUSED": "Пауза",
    "WAITING_PARTS": "Ожидание запчастей",
    "COMPLETED": "Завершено"
}


class RepairTaskAdmin(BaseModelView, model=RepairTask):

    list_template = "admin_task_list.html"

    column_list = [
        RepairTask.id,
        RepairTask.rolling_stock,
        RepairTask.repair_type,
        RepairTask.brigade,
        RepairTask.status,
        RepairTask.start_date,
        RepairTask.planned_end_date
    ]

    column_labels = {
        "id": "ID",
        "rolling_stock": "Серия МВПС",
        "repair_type": "Вид ремонта",
        "brigade": "Бригада",
        "status": "Статус ремонта",
        "start_date": "Дата начала",
        "baseline_end_date": "Базовый план (по регламенту)",
        "planned_end_date": "Текущий план (с учетом пауз)",
        "master_name_snapshot": "ФИО Мастера",
        "actual_end_date": "Фактическое окончание",
        "formatted_paused_time": "Суммарное время пауз"
    }

    _shared_formatters = {
        RepairTask.status: lambda m, a: TASK_STATUS_TRANSLATE.get(
            m.status.name if hasattr(m.status, 'name') else str(m.status),
            str(m.status)
        ),
        RepairTask.start_date:
            lambda m, a: m.start_date.strftime("%d.%m.%Y %H:%M") if getattr(m, 'start_date', None) else "—",

        "baseline_end_date":
            lambda m, a: m.baseline_end_date.strftime("%d.%m.%Y %H:%M") if getattr(m, 'baseline_end_date', None) else "—",

        RepairTask.planned_end_date:
            lambda m, a: m.planned_end_date.strftime("%d.%m.%Y %H:%M") if getattr(m, 'planned_end_date', None) else "—",

        RepairTask.actual_end_date:
            lambda m, a: m.actual_end_date.strftime("%d.%m.%Y %H:%M") if getattr(m, 'actual_end_date', None) else "—",
    }

    column_formatters = _shared_formatters
    column_formatters_detail = _shared_formatters

    column_details_list = [
        RepairTask.id,
        RepairTask.rolling_stock,
        RepairTask.repair_type,
        RepairTask.brigade,
        RepairTask.status,
        RepairTask.start_date,

        "baseline_end_date",
        "formatted_paused_time",

        RepairTask.planned_end_date,
        RepairTask.actual_end_date
    ]

    name = "Задание"
    name_plural = "Ремонтные задания"
    icon = "fa-solid fa-clipboard-list"

    can_create = False
    can_edit = False
    can_delete = True

    async def delete_model(self, request: Request, pk: Any) -> None:
        async with DBManager(session_factory=async_session_maker) as db:
            service = RepairTaskService(db)
            try:
                await service.delete_task(int(pk))
            except HTTPException as e:
                raise Exception(e.detail)
            except Exception as e:
                raise Exception(str(e))

class RepairStageAdmin(BaseModelView, model=RepairStage):
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
        planned_30_days_count = 0

        in_progress_count = 0
        paused_count = 0
        overdue_tasks_count = 0
        active_tasks_data = []

        status_distribution = {
            "Создано": 0,
            "В работе": 0,
            "Пауза": 0,
            "Ожидание запчастей": 0,
            "Ожидает закрытия": 0
        }

        async with DBManager(session_factory=async_session_maker) as db:
            service = PlanningService(db)

            trains = await db.trains.get_all(limit=1000)
            total_trains = len(trains)

            for train in trains:
                plan_info = await service.get_train_planning_status(train.id)
                if plan_info and plan_info["planning"]:
                    planning_data.append(plan_info)
                    for p in plan_info["planning"]:
                        if 0 <= p["days_remaining"] <= 30:
                            planned_30_days_count += 1

            active_tasks = await db.tasks.get_active_tasks()

            now = datetime.now(timezone.utc)

            for task in active_tasks:
                status_val = task.status.value
                if status_val in status_distribution:
                    status_distribution[status_val] += 1

                if task.status == TaskStatusEnum.IN_PROGRESS:
                    in_progress_count += 1
                elif task.status in [TaskStatusEnum.PAUSED, TaskStatusEnum.WAITING_PARTS]:
                    paused_count += 1

                is_task_overdue = False
                if task.planned_end_date and task.planned_end_date < now:
                    is_task_overdue = True
                    overdue_tasks_count += 1

                active_tasks_data.append({
                    "task": task,
                    "is_task_overdue": is_task_overdue
                })

            filtered_labels = [k for k, v in status_distribution.items() if v > 0]
            filtered_values = [v for k, v in status_distribution.items() if v > 0]

            chart_data_json = json.dumps({
                "labels": filtered_labels,
                "values": filtered_values
            })

            return await self.templates.TemplateResponse(
                request,
                "dashboard.html",
                context={
                    "request": request,
                    "total_trains": total_trains,
                    "planned_30_days_count": planned_30_days_count,
                    "in_progress_count": in_progress_count,
                    "paused_count": paused_count,
                    "overdue_tasks_count": overdue_tasks_count,
                    "active_tasks": active_tasks_data,
                    "chart_data": chart_data_json
                }
            )

    @expose("/dashboard/task/{task_id}", methods=["GET"])
    async def task_details(self, request: Request):
        task_id = request.path_params.get("task_id")

        async with DBManager(session_factory=async_session_maker) as db:
            service = RepairTaskService(db)
            try:
                task = await service.get_full_task(int(task_id))
                brigades = await db.brigades.get_all()

                return await self.templates.TemplateResponse(
                    request,
                    "admin_task_details.html",
                    context={
                        "request": request,
                        "task": task,
                        "brigades": brigades
                    }
                )
            except Exception as e:
                print(f"Ошибка при рендере деталей задачи: {str(e)}")
                return RedirectResponse(url="/admin/dashboard?error=Error loading task", status_code=303)

    @expose("/dashboard/train/{train_id}", methods=["GET"])
    async def train_details(self, request: Request):
        train_id = request.path_params.get("train_id")

        async with DBManager(session_factory=async_session_maker) as db:
            train = await db.trains.get_by_id(int(train_id))
            if not train:
                return RedirectResponse(url="/admin/dashboard?error=Train not found", status_code=303)

            planning_service = PlanningService(db)
            plan_info = await planning_service.get_train_planning_status(train.id)

            history_tasks = await db.tasks.get_history_by_train(train.id)
            active_tasks = await db.tasks.get_active_by_train(train.id)

            return await self.templates.TemplateResponse(
                request,
                "admin_train_details.html",
                context={
                    "request": request,
                    "train": train,
                    "planning": plan_info["planning"] if plan_info else [],
                    "history": history_tasks,
                    "active_tasks": active_tasks,
                    "total_completed": len(history_tasks)
                }
            )

    @expose("/dashboard/task/{task_id}/reject", methods=["POST"])
    async def reject_task_action(self, request: Request):
        task_id = request.path_params.get("task_id")
        form = await request.form()
        comment = form.get("comment")

        async with DBManager(session_factory=async_session_maker) as db:
            service = RepairTaskService(db)
            try:
                await service.reject_closure(int(task_id), comment)
            except Exception as e:
                error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
                return RedirectResponse(url=f"/admin/dashboard?error={error_msg}", status_code=303)

        return RedirectResponse(url=f"/admin/dashboard/task/{task_id}", status_code=303)

    @expose("/dashboard/task/{task_id}/approve", methods=["POST"])
    async def approve_task_action(self, request: Request):
        task_id = request.path_params.get("task_id")

        async with DBManager(session_factory=async_session_maker) as db:
            service = RepairTaskService(db)
            try:
                await service.approve_closure(int(task_id))
            except Exception as e:
                error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
                return RedirectResponse(url=f"/admin/dashboard?error={error_msg}", status_code=303)

        return RedirectResponse(url="/admin/archive", status_code=303)

    @expose("/dashboard/upcoming-repairs", methods=["GET"])
    async def upcoming_repairs(self, request: Request):
        all_upcoming = []

        async with DBManager(session_factory=async_session_maker) as db:
            service = PlanningService(db)

            trains = await db.trains.get_all(limit=1000)

            for train in trains:
                plan_info = await service.get_train_planning_status(train.id)
                if plan_info and plan_info["planning"]:
                    for p in plan_info["planning"]:
                        all_upcoming.append({
                            "train_id": train.id,
                            "series": train.series,
                            "inventory_number": train.inventory_number,
                            "repair_type": p["repair_type"],
                            "last_repair_date": p["last_repair_date"],
                            "next_repair_date": p["next_repair_date"],
                            "days_remaining": p["days_remaining"],
                            "is_overdue": p["is_overdue"]
                        })

            all_upcoming.sort(key=lambda x: x["days_remaining"])

            return await self.templates.TemplateResponse(
                request,
                "admin_upcoming_repairs.html",
                context={
                    "request": request,
                    "upcoming": all_upcoming
                }
            )



class CreateTaskAdminView(BaseView):
    name = "Создать задание"
    icon = "fa-solid fa-plus-circle"

    def is_visible(self, request: Request) -> bool:
        return False

    @expose("/create-task", methods=["GET"])
    async def create_task_page(self, request: Request):
        async with DBManager(session_factory=async_session_maker) as db:

            trains = await db.trains.get_all(limit=1000)
            brigades = await db.brigades.get_all(limit=1000)

            return await self.templates.TemplateResponse(
                request,
                "admin_create_task.html",
                context={
                    "request": request,
                    "trains": trains,
                    "brigades": brigades,
                    "error": request.query_params.get("error")
                }
            )

    @expose("/create-task", methods=["POST"])
    async def create_task_action(self, request: Request):
        form = await request.form()

        try:
            task_in = RepairTaskCreate(
                rolling_stock_id=int(form.get("rolling_stock_id")),
                repair_type=form.get("repair_type"),
                brigade_id=int(form.get("brigade_id"))
            )

            async with DBManager(session_factory=async_session_maker) as db:
                service = RepairTaskService(db)
                await service.create_task(task_in)

            return RedirectResponse(url="/admin/dashboard", status_code=303)

        except Exception as e:
            error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
            return RedirectResponse(url=f"/admin/create-task?error={error_msg}", status_code=303)


class ArchiveView(BaseView):
    name = "Архив ремонтов"
    icon = "fa-solid fa-box-archive"

    @expose("/archive", methods=["GET"])
    async def archive_page(self, request: Request):
        search = request.query_params.get("search", "").strip()

        async with DBManager(session_factory=async_session_maker) as db:
            completed_tasks = await db.tasks.get_archived_tasks(limit=1000, search=search)

            return await self.templates.TemplateResponse(
                request,
                "admin_archive.html",
                context={
                    "request": request,
                    "tasks": completed_tasks,
                    "search_query": search
                }
            )


class UserAdmin(BaseModelView, model=User):
    column_list = [User.id, User.username, User.role]

    column_labels = {
        "id": "ID",
        "username": "Логин",
        "role": "Роль",
        "hashed_password": "Пароль"
    }

    form_overrides = {
        "role": SelectField
    }

    form_args = {
        "role": {
            "choices": [
                ("master", "Мастер"),
                ("engineer", "Инженер"),
                ("admin", "Администратор")
            ]
        }
    }

    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    column_searchable_list = [User.username]

    async def insert_model(self, request: Request, data: dict) -> Any:
        raw_password = data.get("hashed_password")
        if raw_password:
            data["hashed_password"] = get_password_hash(raw_password)
        return await super().insert_model(request, data)

    async def update_model(self, request: Request, data: dict, model: Any) -> Any:
        raw_password = data.get("hashed_password")
        if raw_password and not raw_password.startswith("$2b$"):
            data["hashed_password"] = get_password_hash(raw_password)
        return await super().update_model(request, data, model)