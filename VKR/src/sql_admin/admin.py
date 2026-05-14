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
from fastapi.responses import RedirectResponse
from src.schemas.repair_tasks import RepairTaskCreate
from src.services.repair_tasks import RepairTaskService
from src.models.enums import RepairTypeEnum
from src.schemas.regulations import RegulationCreate, RegulationTemplateCreate
from src.services.catalogs import RegulationService


class RollingStockAdmin(ModelView, model=RollingStock):
    column_list = [RollingStock.id, RollingStock.inventory_number, RollingStock.series, RollingStock.manufacture_date]
    name = "Поезд (МВПС)"
    name_plural = "Поезда (МВПС)"
    icon = "fa-solid fa-train"
    column_searchable_list = [RollingStock.inventory_number, RollingStock.series]
    form_excluded_columns = ["repair_tasks"]


class RegulationAdmin(ModelView, model=Regulation):
    column_list = [Regulation.id, Regulation.repair_type, Regulation.train_series, Regulation.standard_hours,
                   Regulation.frequency_days]
    name = "Регламент"
    name_plural = "Регламенты"
    icon = "fa-solid fa-book"
    can_create = False
    list_template = "admin_regulation_list.html"
    form_excluded_columns = ["stages", "templates"]


class CreateRegulationAdminView(BaseView):
    name = "Создать регламент"
    icon = "fa-solid fa-file-signature"

    def is_visible(self, request: Request) -> bool:
        return False

    @expose("/create-regulation", methods=["GET"])
    async def create_regulation_page(self, request: Request):
        async with DBManager(session_factory=async_session_maker) as db:
            # Получаем только существующие и уникальные серии поездов
            trains_query = select(RollingStock.series).distinct()
            train_series = (await db.session.execute(trains_query)).scalars().all()

            # Достаем доступные типы ремонта из нашего Enum
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
            # Парсим динамические этапы из формы
            templates = []

            # Выделяем все ключи формы, относящиеся к этапам
            template_keys = [k for k in form.keys() if k.startswith("template_name_")]
            # Сортируем по суффиксу-индексу, чтобы гарантировать порядок
            template_keys.sort(key=lambda x: int(x.split("_")[-1]))

            # enumerate с 1 обеспечивает строгое соответствие валидатору order_number в Pydantic
            for i, key in enumerate(template_keys, start=1):
                name = form.get(key)
                if name and name.strip():
                    templates.append(
                        RegulationTemplateCreate(name=name.strip(), order_number=i)
                    )

            if not templates:
                raise ValueError("Необходимо добавить хотя бы один этап ремонта.")

            # Собираем Pydantic схему
            reg_in = RegulationCreate(
                repair_type=form.get("repair_type"),
                train_series=form.get("train_series"),
                standard_hours=int(form.get("standard_hours")),
                frequency_days=int(form.get("frequency_days", 0)),
                templates=templates
            )

            # Передаем схему в уже написанный сервисный слой
            async with DBManager(session_factory=async_session_maker) as db:
                service = RegulationService(db)
                await service.create(reg_in)

            return RedirectResponse(url="/admin/dashboard", status_code=303)

        except Exception as e:
            # Ловим ошибки бизнес-логики (например, дубликаты)
            error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
            return RedirectResponse(url=f"/admin/create-regulation?error={error_msg}", status_code=303)

class PartAndMaterialAdmin(ModelView, model=PartAndMaterial):
    column_list = [PartAndMaterial.id, PartAndMaterial.nomenclature, PartAndMaterial.stock_quantity]
    name = "Запчасть"
    name_plural = "Склад запчастей"
    icon = "fa-solid fa-box"
    column_searchable_list = [PartAndMaterial.nomenclature]
    form_excluded_columns = ["stage_associations"]

class WorkBrigadeAdmin(ModelView, model=WorkBrigade):
    column_list = [WorkBrigade.id, WorkBrigade.name]
    name = "Бригада"
    name_plural = "Рабочие бригады"
    icon = "fa-solid fa-users"
    form_excluded_columns = [WorkBrigade.stages, WorkBrigade.repair_tasks]

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
        overdue_stages_count = 0
        active_tasks_data = []

        # 1. Открываем транзакцию через наш менеджер
        async with DBManager(session_factory=async_session_maker) as db:
            service = PlanningService(db)

            # --- БЛОК ПЛАНИРОВАНИЯ ---
            trains_query = select(RollingStock)
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
                    overdue_stages_count += 1

                active_tasks_data.append({
                    "task": task,
                    "is_task_overdue": is_task_overdue
                })

            chart_data_json = json.dumps({
                "labels": chart_labels,
                "values": chart_values
            })

            # ВАЖНО: Делаем рендер и формирование JSON ДО выхода из блока async with!
            return await self.templates.TemplateResponse(
                request,
                "dashboard.html",
                context={
                    "request": request,
                    "planning_data": planning_data,
                    "chart_data": chart_data_json,
                    "total_trains": total_trains,
                    "in_progress_count": in_progress_count,
                    "paused_count": paused_count,
                    "active_tasks": active_tasks_data,
                    "overdue_stages_count": overdue_stages_count
                }
            )

    @expose("/dashboard/task/{task_id}", methods=["GET"])
    async def task_details(self, request: Request):
        task_id = request.path_params.get("task_id")

        async with DBManager(session_factory=async_session_maker) as db:
            service = RepairTaskService(db)
            try:
                # Используем уже существующий метод сервиса для получения графа задачи
                task = await service.get_full_task(int(task_id))

                return await self.templates.TemplateResponse(
                    request,
                    "admin_task_details.html",
                    context={
                        "request": request,
                        "task": task,
                    }
                )
            except Exception as e:
                return RedirectResponse(url="/admin/dashboard?error=Task not found", status_code=303)



class CreateTaskAdminView(BaseView):
    name = "Создать задание"
    icon = "fa-solid fa-plus-circle"

    @expose("/create-task", methods=["GET"])
    async def create_task_page(self, request: Request):
        async with DBManager(session_factory=async_session_maker) as db:
            trains_query = select(RollingStock)
            brigades_query = select(WorkBrigade)

            trains = (await db.session.execute(trains_query)).scalars().all()
            brigades = (await db.session.execute(brigades_query)).scalars().all()

            # ВАЖНО: Рендерим шаблон прямо здесь, не выходя из блока with
            return await self.templates.TemplateResponse(
                request,
                "admin_create_task.html",
                context={
                    "request": request,
                    "trains": trains,
                    "brigades": brigades,
                    "error": request.query_params.get("error")  # Для вывода ошибок
                }
            )

    @expose("/create-task", methods=["POST"])
    async def create_task_action(self, request: Request):
        form = await request.form()

        try:
            # Собираем данные из HTML-формы в нашу Pydantic схему
            task_in = RepairTaskCreate(
                rolling_stock_id=int(form.get("rolling_stock_id")),
                repair_type=form.get("repair_type"),
                brigade_id=int(form.get("brigade_id"))
            )

            # Вызываем сервис, который сделает всю магию с этапами
            async with DBManager(session_factory=async_session_maker) as db:
                service = RepairTaskService(db)
                await service.create_task(task_in)

            # Если всё ок - редиректим на список задач в админке
            return RedirectResponse(url="/admin/dashboard", status_code=303)

        except Exception as e:
            # Если ошибка (например, нет регламента) - возвращаем обратно с текстом ошибки
            error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
            return RedirectResponse(url=f"/admin/create-task?error={error_msg}", status_code=303)