from typing import Protocol, Self

from src.modules.rewards.application.ports.reward_repository import RewardRepository
from src.modules.users.application.ports.user_repository import UserRepository
from src.shared.outbox.application.repositories import OutboxRepository


class UnitOfWork(Protocol):
    """Единая транзакционная граница.

    Новый модуль -> добавить сюда атрибут с типом порта репозитория,
    а в SQLAlchemyUnitOfWork.__aenter__ - его создание.
    Оба места правятся вместе, иначе протокол разойдётся с реализацией.
    """

    users: UserRepository
    outbox: OutboxRepository
    rewards: RewardRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(self, exc_type, exc_value, traceback): ...

    async def commit(self): ...

    async def rollback(self): ...

    async def flush(self): ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork: ...
