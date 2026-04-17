import asyncio
from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.database import async_session_maker
from src.models.enums import RepairTypeEnum, TaskStatusEnum, StageStatusEnum
from src.models.parts_and_materials import PartAndMaterial
from src.models.regulations import Regulation
from src.models.repair_stages import RepairStage
from src.models.repair_tasks import RepairTask
from src.models.rolling_stocks import RollingStock
from src.models.work_brigades import WorkBrigade
from src.models.stage_parts import StagePart
import time


async def run_simulation():
    print("🚀 Запуск симуляции жизненного цикла ремонта...\n")

    async with async_session_maker() as session:  # [cite: 1]

        # ==========================================
        # БЛОК 1: Создание нормативно-справочной базы
        # ==========================================
        print("1. Подготовка справочников (Бригады, Запчасти, Нормативы)...")

        # Функция-помощник для поиска или создания
        async def get_or_create_part(name: str, qty: int):
            query = select(PartAndMaterial).where(PartAndMaterial.nomenclature == name)
            part = (await session.execute(query)).scalar_one_or_none()
            if not part:
                part = PartAndMaterial(nomenclature=name, stock_quantity=qty)
                session.add(part)
            return part

        part_wheel = await get_or_create_part("Колесная пара ТИП-А", 10)
        part_oil = await get_or_create_part("Масло трансмиссионное (бочка)", 5)

        # То же самое для бригады
        query_brigade = select(WorkBrigade).where(WorkBrigade.name == "Бригада Слесарей №1")
        brigade_alpha = (await session.execute(query_brigade)).scalar_one_or_none()
        if not brigade_alpha:
            brigade_alpha = WorkBrigade(name="Бригада Слесарей №1")
            session.add(brigade_alpha)

        # То же самое для норматива
        query_reg = select(Regulation).where(Regulation.repair_type == RepairTypeEnum.TO3)
        reg_to3 = (await session.execute(query_reg)).scalar_one_or_none()
        if not reg_to3:
            reg_to3 = Regulation(repair_type=RepairTypeEnum.TO3, standard_hours=24)
            session.add(reg_to3)

        await session.commit()
        print("✅ Справочники загружены (или найдены существующие).\n")

        # ==========================================
        # БЛОК 2: Создание МВПС и Ремонтного задания
        # ==========================================
        print("2. Приемка поезда и постановка задачи...")

        unique_id = int(time.time())  # Генерируем уникальный хвост
        train_number = f"МВПС-1024-{unique_id}"

        # Создаем вагон с уникальным инвентарным номером
        train = RollingStock(
            inventory_number=train_number,
            series="ЭД4М",
            manufacture_date=date(2015, 5, 10)
        )
        session.add(train)
        await session.flush()

        # Создаем ремонтное задание для этого вагона
        task = RepairTask(
            rolling_stock_id=train.id,
            repair_type=RepairTypeEnum.TO3,
            status=TaskStatusEnum.CREATED  # [cite: 8]
        )
        session.add(task)
        await session.commit()
        print(f"✅ Создано задание ID: {task.id} для поезда {train.inventory_number}.\n")

        # ==========================================
        # БЛОК 3: Планирование этапов и назначение ресурсов
        # ==========================================
        print("3. Назначение этапа, бригады и списание запчастей...")

        # Создаем этап: Диагностика ходовой части
        stage_diag = RepairStage(
            repair_task_id=task.id,
            regulation_id=reg_to3.id,
            name="Диагностика и замена колесной пары",
            status=StageStatusEnum.IN_PROGRESS,
            start_time=datetime.now(timezone.utc)
        )

        # Магия ORM: Добавляем связи M:N через списки (Алхимия сама заполнит ассоциативные таблицы)
        stage_diag.brigades.append(brigade_alpha)

        # Добавляем 2 колесные пары
        sp_wheel = StagePart(part=part_wheel, quantity_used=2)
        # Добавляем 5 литров масла
        sp_oil = StagePart(part=part_oil, quantity_used=5)

        stage_diag.part_associations.extend([sp_wheel, sp_oil])

        session.add(stage_diag)
        await session.commit()
        print("✅ Этап назначен, бригада и запчасти прикреплены.\n")

        # ==========================================
        # БЛОК 4: Имитация завершения работы
        # ==========================================
        print("4. Имитация завершения работы...")

        # Обновляем статусы
        stage_diag.status = StageStatusEnum.COMPLETED
        stage_diag.end_time = datetime.now(timezone.utc)

        task.status = TaskStatusEnum.COMPLETED
        task.actual_end_date = datetime.now(timezone.utc)

        await session.commit()
        print("✅ Ремонт успешно завершен.\n")

        # ==========================================
        # БЛОК 5: Проверка чтения данных (Жадная загрузка)
        # ==========================================
        print("5. Извлечение данных для проверки графа связей...")

        # Строим сложный запрос: Достаем вагон со всеми его заданиями, этапами, бригадами и запчастями!
        stmt = (
            select(RollingStock)
            # ИСПРАВЛЕНИЕ 1: Ищем именно тот вагон, который только что создали!
            .where(RollingStock.inventory_number == train_number)
            .options(
                selectinload(RollingStock.repair_tasks)
                .selectinload(RepairTask.stages)
                .selectinload(RepairStage.brigades)
            )
            .options(
                selectinload(RollingStock.repair_tasks)
                .selectinload(RepairTask.stages)
                # ИСПРАВЛЕНИЕ 2: Обращаемся к новому имени связи
                .selectinload(RepairStage.part_associations)
                # ИСПРАВЛЕНИЕ 3: Подтягиваем саму деталь (PartAndMaterial) из промежуточной модели
                .selectinload(StagePart.part)
            )
        )

        result = await session.execute(stmt)
        fetched_train = result.scalar_one_or_none()

        if fetched_train:
            print("\n--- ОТЧЕТ ПО ПОЕЗДУ ---")
            print(f"Поезд: {fetched_train.series} ({fetched_train.inventory_number})")
            for t in fetched_train.repair_tasks:
                print(f"  Задание: {t.repair_type.value}, Статус: {t.status.value}")
                for s in t.stages:
                    print(f"    Этап: {s.name} ({s.status.value})")
                    brigades_str = ", ".join([b.name for b in s.brigades])
                    print(f"      Бригады: {brigades_str}")
                    # Здесь у тебя всё было написано правильно!
                    parts_str = ", ".join(
                        [f"{pa.part.nomenclature} ({pa.quantity_used} шт.)" for pa in s.part_associations])
                    print(f"      Детали: {parts_str}")
        print("-----------------------\n")



if __name__ == "__main__":
    asyncio.run(run_simulation())