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


async def run_simulation():
    print("🚀 Запуск симуляции жизненного цикла ремонта...\n")

    async with async_session_maker() as session:  # [cite: 1]

        # ==========================================
        # БЛОК 1: Создание нормативно-справочной базы
        # ==========================================
        print("1. Подготовка справочников (Бригады, Запчасти, Нормативы)...")

        brigade_alpha = WorkBrigade(name="Бригада Слесарей №1")
        part_wheel = PartAndMaterial(nomenclature="Колесная пара ТИП-А", stock_quantity=10)
        part_oil = PartAndMaterial(nomenclature="Масло трансмиссионное (бочка)", stock_quantity=5)

        # Создаем норматив для ремонта ТО-3
        reg_to3 = Regulation(repair_type=RepairTypeEnum.TO3, standard_hours=24)  # [cite: 7]

        session.add_all([brigade_alpha, part_wheel, part_oil, reg_to3])
        await session.commit()
        print("✅ Справочники загружены.\n")

        # ==========================================
        # БЛОК 2: Создание МВПС и Ремонтного задания
        # ==========================================
        print("2. Приемка поезда и постановка задачи...")

        # Создаем вагон
        train = RollingStock(
            inventory_number="МВПС-1024-А",
            series="ЭД4М",
            manufacture_date=date(2015, 5, 10)  # [cite: 9]
        )
        session.add(train)
        await session.flush()  # flush отправляет данные в БД, чтобы получить train.id, но транзакция еще открыта

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
        stage_diag.parts.append(part_wheel)
        stage_diag.parts.append(part_oil)

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
            .where(RollingStock.inventory_number == "МВПС-1024-А")
            # Используем selectinload для подгрузки связанных коллекций без проблемы "n+1 запросов"
            .options(
                selectinload(RollingStock.repair_tasks)
                .selectinload(RepairTask.stages)
                .selectinload(RepairStage.brigades)
            )
            .options(
                selectinload(RollingStock.repair_tasks)
                .selectinload(RepairTask.stages)
                .selectinload(RepairStage.parts)
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
                    parts_str = ", ".join([p.nomenclature for p in s.parts])
                    print(f"      Детали: {parts_str}")
        print("-----------------------\n")


if __name__ == "__main__":
    asyncio.run(run_simulation())