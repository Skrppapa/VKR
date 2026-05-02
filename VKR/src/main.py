import sys
import uvicorn
from fastapi import FastAPI
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.api.routers.rolling_stock import router as rolling_stock_router
from src.api.routers.catalogs import router as catalogs_router
from src.api.routers.repair_task import router as repair_task_router
from src.api.routers.repair_stage import router as repair_stage_router



from sqladmin import Admin
from src.database import engine
from src.admin import DashboardView
from src.admin import (
    RollingStockAdmin, RegulationAdmin,
    PartAndMaterialAdmin, WorkBrigadeAdmin,
    RepairTaskAdmin, RepairStageAdmin
)


app = FastAPI(
    title="Система управления ремонтом МВПС",
    description="API для планирования и контроля ремонта подвижного состава",
    version="1.0.0"
)

#===========Импорты==========
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_path = os.path.join(BASE_DIR, "templates")
#===========Импорты==========


admin = Admin(
    app,
    engine,
    title="Панель Управления Депо",
    templates_dir=templates_path
)


admin.add_view(DashboardView)
admin.add_view(RollingStockAdmin)
admin.add_view(RegulationAdmin)
admin.add_view(PartAndMaterialAdmin)
admin.add_view(WorkBrigadeAdmin)
admin.add_view(RepairTaskAdmin)
admin.add_view(RepairStageAdmin)


app.include_router(rolling_stock_router, prefix="/api/v1")
app.include_router(catalogs_router, prefix="/api/v1")
app.include_router(repair_task_router, prefix="/api/v1")
app.include_router(repair_stage_router, prefix="/api/v1")





if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)


