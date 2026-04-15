import enum


# Справочники (Enums) для строгой типизации

class RepairTypeEnum(str, enum.Enum):
    TO1 = "ТО-1"
    TO2 = "ТО-2"
    TO3 = "ТО-3"
    TR1 = "ТР-1"
    TR2 = "ТР-2"
    KR = "КР"


class TaskStatusEnum(str, enum.Enum):
    CREATED = "Создано"
    IN_PROGRESS = "В работе"
    COMPLETED = "Завершено"


class StageStatusEnum(str, enum.Enum):
    PENDING = "Ожидание"
    IN_PROGRESS = "В работе"
    WAITING_PARTS = "Ожидание запчастей"
    COMPLETED = "Завершено"