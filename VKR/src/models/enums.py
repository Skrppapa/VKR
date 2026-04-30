import enum

# Справочники: Виды ремонта, Статусы задач и стадий ремонта

class RepairTypeEnum(str, enum.Enum):
    TO1 = "ТО-1"
    TO2 = "ТО-2"
    TO3 = "ТО-3"
    TR1 = "ТР-1"
    TR2 = "ТР-2"
    TR3 = "ТР-3"
    KR1 = "КР-1"
    KR2 = "КР-2"

class TaskStatusEnum(str, enum.Enum):
    CREATED = "Создано"
    IN_PROGRESS = "В работе"
    WAITING_PARTS = "Ожидание запчастей"
    PAUSED = "Пауза"
    COMPLETED = "Завершено"

class StageStatusEnum(str, enum.Enum):
    PENDING = "Ожидание"
    IN_PROGRESS = "В работе"
    WAITING_PARTS = "Ожидание запчастей"
    PAUSED = "Пауза"
    COMPLETED = "Завершено"

