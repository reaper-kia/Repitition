import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from src.core.config import settings
from src.shared.infra.database.base import Base

# Регистрация моделей в Base.metadata — без этого create_all() не увидит
# таблицы, которые нигде больше не импортируются в процессе тестов.
from src.modules.users.infra.models import UserModel  # noqa: F401
from src.shared.outbox.infra.models import OutboxMessageModel  # noqa: F401
from src.modules.club.infra.models import ClubModel  # noqa: F401
from src.modules.client.infra.models import ClientModel, PurchaseModel  # noqa: F401
from src.modules.rewards.infra.models import RewardBudgetModel  # noqa: F401
from src.modules.rewards.infra.models import BudgetReservationModel  # noqa: F401
from src.modules.rewards.infra.models import DiscountGrantModel  # noqa: F401


_db_available_cache: bool | None = None


async def _check_db() -> bool:
    try:
        engine = create_async_engine(settings.database_url)
        async with engine.connect():
            pass
        await engine.dispose()
        return True
    except Exception:  # noqa: BLE001 — недоступность БД может быть любой
        return False


def _db_available() -> bool:
    global _db_available_cache
    if _db_available_cache is None:
        _db_available_cache = asyncio.run(_check_db())
    return _db_available_cache


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Интеграционные тесты нужен реальный Postgres. Если settings.database_url
    недоступен (локальный прогон без docker compose up) — пропускаем их,
    а не роняем весь набор."""
    if _db_available():
        return
    skip_reason = pytest.mark.skip(
        reason="Postgres недоступен по settings.database_url — "
        "integration-тесты пропущены. Запусти внутри контейнера: "
        "docker compose exec app pytest"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_reason)


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(settings.database_url)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "TRUNCATE TABLE reward_budgets, budget_reservations, "
                "discount_grants CASCADE"
            )
        )
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine, expire_on_commit=False) as s:
        yield s
        await s.rollback()
