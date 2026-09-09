from typing import Protocol
from uuid import UUID

from src.modules.rewards.application.read_models import RewardsReadModel
from src.modules.rewards.domain.entities import Rewards


class RewardsRepository(Protocol):
    async def get_by_id(self, id: UUID) -> Rewards | None: ...

    async def add(self, entity: Rewards) -> None: ...


class RewardsReadRepository(Protocol):
    async def get_by_id(self, id: UUID) -> RewardsReadModel | None: ...
