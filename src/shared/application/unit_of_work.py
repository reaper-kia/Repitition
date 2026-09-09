from types import TracebackType
from typing import Protocol, Self

from src.modules.client.application.ports.client_read_repository import (
    ClientReadRepository,
)
from src.modules.client.application.ports.client_repository import ClientRepository
from src.modules.client.application.ports.club_snapshot_repository import (
    ClubSnapshotRepository,
)
from src.modules.club.application.ports.club_read_repository import ClubReadRepository
from src.modules.club.application.ports.club_repository import ClubRepository
from src.modules.rewards.application.ports.reward_repository import RewardRepository
from src.modules.users.application.ports.user_repository import UserRepository
from src.shared.outbox.application.repositories import OutboxRepository


class UnitOfWork(Protocol):
    users: UserRepository
    rewards: RewardRepository

    clubs: ClubRepository
    clubs_read: ClubReadRepository

    clients: ClientRepository
    clients_read: ClientReadRepository
    club_snapshots: ClubSnapshotRepository

    outbox: OutboxRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def flush(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork: ...
