import os

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key")
os.environ.setdefault("ADMIN_REGISTRATION_CODE", "test-admin-code")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "hackathon")          # было test_db
os.environ.setdefault("POSTGRES_USER", "hackathon")        # было test_user
os.environ.setdefault("POSTGRES_PASSWORD", "hackathon")    # подставь свой из .env
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://hackathon:hackathon@localhost:5432/hackathon",  # тот же контейнер
)

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.shared.infra.database.base import Base

# импортируем модели, чтобы они зарегистрировались в Base.metadata
import src.modules.users.infra.models          # noqa: F401
import src.modules.rewards.infra.models         # noqa: F401
import src.modules.engagement.infra.models      # noqa: F401
import src.shared.outbox.infra.models           # noqa: F401


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(os.environ["DATABASE_URL"])
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    # чистим наши таблицы после каждого теста
    async with engine.begin() as conn:
        await conn.exec_driver_sql(
            "TRUNCATE discount_grants, budget_reservations, "
            "reward_budgets, retention_cases CASCADE"
        )

@pytest_asyncio.fixture(autouse=True)
async def _clean_rewards_tables(engine):
    yield
    async with engine.begin() as conn:
        await conn.exec_driver_sql(
            "TRUNCATE discount_grants, budget_reservations, "
            "reward_budgets, retention_cases CASCADE"
        )