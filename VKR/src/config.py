from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # Определяем абсолютный путь до корня проекта

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # JWT_SECRET_KEY: str  # Ключ генерации
    # JWT_ALGORITHM: str   # Алгоритм генерации
    # ACCESS_TOKEN_EXPIRE_MINUTES: int  # Время жизни токена
    #
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")   # env_file=".env" - указываем явно откуда Pydantic читает переменные окружения (по умолчанию читает из .env)
    #                                                      # extra='ignore' - игнорируем если в .env есть переменные которые в классе выше не использованы

settings = Settings()