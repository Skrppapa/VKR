import sys
import os
import uvicorn
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


from src.api.rolling_stock import router as rolling_stock_router
from src.api.catalogs import router as catalogs_router
from src.api.repair_task import router as repair_task_router
from src.api.repair_stage import router as repair_stage_router
from src.api.auth import router as auth
from src.api.pages import router as pages
from src.security import get_current_user
from src.utils.logger import log
import time

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
                                 CreateRegulationAdminView,
                                 ArchiveView,
                                 UserAdmin)


app = FastAPI(
    title="Система управления ремонтом МВПС",
    description="API для планирования и контроля ремонта подвижного состава",
    version="1.0.0"
)

os.makedirs("media/docs", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    client_ip = request.client.host if request.client else "Unknown"
    log.info(f"Incoming request: {request.method} {request.url.path} from {client_ip}")

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000

    if response.status_code >= 500:
        log.error(f"Response: {response.status_code} | Time: {process_time:.2f}ms | Path: {request.url.path}")
    elif response.status_code >= 400:
        log.warning(f"Response: {response.status_code} | Time: {process_time:.2f}ms | Path: {request.url.path}")
    else:
        log.info(f"Response: {response.status_code} | Time: {process_time:.2f}ms | Path: {request.url.path}")

    return response

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_path = os.path.join(BASE_DIR, "templates")


authentication_backend = AdminAuth(secret_key="another-super-secret-key")

admin = Admin(
    app,
    engine,
    title="Панель управления депо",
    templates_dir=templates_path,
    authentication_backend=authentication_backend
)


admin.add_view(DashboardView)
admin.add_view(ArchiveView)
admin.add_view(CreateRegulationAdminView)
admin.add_view(CreateTaskAdminView)
admin.add_view(RollingStockAdmin)
admin.add_view(RegulationAdmin)
admin.add_view(PartAndMaterialAdmin)
admin.add_view(WorkBrigadeAdmin)
admin.add_view(RepairTaskAdmin)
admin.add_view(UserAdmin)




app.include_router(auth, prefix="/api/v1")
app.include_router(rolling_stock_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(catalogs_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(repair_task_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(repair_stage_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(pages)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)


