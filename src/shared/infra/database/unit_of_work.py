from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.modules.client.infra.client_read_repository import (
    SQLAlchemyClientReadRepository,
)
from src.modules.client.infra.club_snapshot_repository import (
    SQLAlchemyClubSnapshotRepository,
)
from src.modules.client.infra.repositories import SQLAlchemyClientRepository
from src.modules.club.infra.repositories import (
    SQLAlchemyClubReadRepository,
    SQLAlchemyClubRepository,
)
from src.modules.rewards.infra.repositories import SQLAlchemyRewardRepository
from src.modules.users.infra.repositories import SQLAlchemyUserRepository
from src.shared.application.unit_of_work import UnitOfWork
from src.shared.outbox.infra.repositories import SQLAlchemyOutboxRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session = self._session_factory()

        self.users = SQLAlchemyUserRepository(self.session)
        self.rewards = SQLAlchemyRewardRepository(self.session)

        self.clubs = SQLAlchemyClubRepository(self.session)
        self.clubs_read = SQLAlchemyClubReadRepository(self.session)

        self.clients = SQLAlchemyClientRepository(self.session)
        self.clients_read = SQLAlchemyClientReadRepository(self.session)
        self.club_snapshots = SQLAlchemyClubSnapshotRepository(self.session)

        self.outbox = SQLAlchemyOutboxRepository(self.session)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()
