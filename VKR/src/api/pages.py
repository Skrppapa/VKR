from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["Фронтенд"])

templates = Jinja2Templates(directory="templates")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/")
async def root_redirect():
    return RedirectResponse(url="/login")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/workspace")
async def master_workspace(request: Request):
    return templates.TemplateResponse("workspace.html", {"request": request})