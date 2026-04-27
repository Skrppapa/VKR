from src.database import Base
from src.models.enums import RepairTypeEnum, TaskStatusEnum, StageStatusEnum
from src.models.rolling_stocks import RollingStock
from src.models.repair_tasks import RepairTask
from src.models.repair_stages import RepairStage
from src.models.work_brigades import WorkBrigade
from src.models.parts_and_materials import PartAndMaterial
from src.models.stage_parts import StagePart
from src.models.regulations import Regulation

# __all__ подсказывает, что именно мы экспортируем из папки models
__all__ = [
    "Base",
    "RollingStock",
    "RepairTask",
    "RepairStage",
    "WorkBrigade",
    "PartAndMaterial",
    "StagePart",
    "Regulation",
    "RepairTypeEnum",
    "TaskStatusEnum",
    "StageStatusEnum",
]