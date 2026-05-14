import sys
import uvicorn
from fastapi import FastAPI, Depends
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.api.rolling_stock import router as rolling_stock_router
from src.api.catalogs import router as catalogs_router
from src.api.repair_task import router as repair_task_router
from src.api.repair_stage import router as repair_stage_router
from src.api.auth import router as auth
from src.api.pages import router as pages
from src.security import get_current_user



from sqladmin import Admin
from src.database import engine
from src.sql_admin.admin_auth import AdminAuth
from src.sql_admin.admin import (RollingStockAdmin,
                                 RegulationAdmin,
                                 PartAndMaterialAdmin,
                                 WorkBrigadeAdmin,
                                 RepairTaskAdmin,
                                 DashboardView,
                                 CreateTaskAdminView,
                                 CreateRegulationAdminView)


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


authentication_backend = AdminAuth(secret_key="another-super-secret-key")

admin = Admin(
    app,
    engine,
    title="Панель Управления Депо",
    templates_dir=templates_path,
    authentication_backend=authentication_backend
)


admin.add_view(DashboardView)
admin.add_view(CreateRegulationAdminView)
admin.add_view(CreateTaskAdminView)
admin.add_view(RollingStockAdmin)
admin.add_view(RegulationAdmin)
admin.add_view(PartAndMaterialAdmin)
admin.add_view(WorkBrigadeAdmin)
admin.add_view(RepairTaskAdmin)



app.include_router(auth, prefix="/api/v1")
app.include_router(rolling_stock_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(catalogs_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(repair_task_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(repair_stage_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(pages)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)


