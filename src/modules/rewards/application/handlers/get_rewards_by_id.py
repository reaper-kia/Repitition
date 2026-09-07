from dataclasses import dataclass

from src.modules.rewards.application.ports.rewards_repository import (
    RewardsReadRepository,
)
from src.modules.rewards.application.queries.get_rewards_by_id import (
    GetRewardsByIdQuery,
)
from src.modules.rewards.domain.exceptions import RewardsNotFoundError


@dataclass
class GetRewardsByIdQueryHandler:
    rewards_read_repository: RewardsReadRepository

    async def handle(self, query: GetRewardsByIdQuery):
        result = await self.rewards_read_repository.get_by_id(query.id)

        if result is None:
            raise RewardsNotFoundError(f"Rewards {query.id} not found")

        return result
