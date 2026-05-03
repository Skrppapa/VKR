from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.api.dependencies import AuthServiceDep

router = APIRouter(prefix="/auth", tags=["Авторизация"])

@router.post("/login")
async def login_for_access_token(
    service: AuthServiceDep,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    return await service.login(form_data.username, form_data.password)