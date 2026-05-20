import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.main import app
from src.database import Base
from src.api.dependencies import get_db
from src.utils.db_manager import DBManager
from src.security import get_current_user
from src.models.users import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
async_session_maker_test = async_sessionmaker(engine_test, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def ac() -> AsyncClient:
    async def override_get_db():
        async with DBManager(session_factory=async_session_maker_test) as db:
            yield db

    async def override_get_current_user():
        return User(id=1, username="test_admin", role="admin")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client