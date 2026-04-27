import sys
import uvicorn
from fastapi import FastAPI
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.api.routers.rolling_stock import router as rolling_stock_router
from src.api.routers.catalogs import router as catalogs_router
from src.api.routers.repair_task import router as repair_task_router
from src.api.routers.repair_stage import router as repair_stage_router


app = FastAPI(
    title="Система управления ремонтом МВПС",
    description="API для планирования и контроля ремонта подвижного состава",
    version="1.0.0"
)


app.include_router(rolling_stock_router, prefix="/api/v1")
app.include_router(catalogs_router, prefix="/api/v1")
app.include_router(repair_task_router, prefix="/api/v1")
app.include_router(repair_stage_router, prefix="/api/v1")



if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)


