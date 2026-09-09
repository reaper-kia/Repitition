from unittest.mock import AsyncMock, MagicMock

import pytest

from src.shared.infra.database.unit_of_work import SQLAlchemyUnitOfWork


def _fake_session() -> MagicMock:
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sqlalchemy_uow_initializes_all_repositories() -> None:
    session = _fake_session()
    session_factory = MagicMock(return_value=session)
    uow = SQLAlchemyUnitOfWork(session_factory)

    entered = await uow.__aenter__()

    assert entered is uow
    assert uow.users is not None
    assert uow.rewards is not None
    assert uow.clubs is not None
    assert uow.clubs_read is not None
    assert uow.clients is not None
    assert uow.clients_read is not None
    assert uow.club_snapshots is not None
    assert uow.outbox is not None

    session_factory.assert_called_once_with()

    await uow.__aexit__(None, None, None)

    session.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sqlalchemy_uow_rolls_back_on_exception() -> None:
    session = _fake_session()
    uow = SQLAlchemyUnitOfWork(MagicMock(return_value=session))

    await uow.__aenter__()
    await uow.__aexit__(RuntimeError, RuntimeError("boom"), None)

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sqlalchemy_uow_commits_and_flushes() -> None:
    session = _fake_session()
    uow = SQLAlchemyUnitOfWork(MagicMock(return_value=session))

    await uow.__aenter__()
    await uow.commit()
    await uow.flush()

    session.commit.assert_awaited_once()
    session.flush.assert_awaited_once()
