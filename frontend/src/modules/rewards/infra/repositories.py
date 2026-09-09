from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.rewards.application.ports.rewards_repository import (
    RewardsReadRepository,
    RewardsRepository,
)
from src.modules.rewards.application.read_models import RewardsReadModel
from src.modules.rewards.domain.entities import Rewards
from src.modules.rewards.infra.models import RewardsModel


class SQLAlchemyRewardsRepository(RewardsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Rewards | None:
        stmt = select(RewardsModel).where(RewardsModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def add(self, entity: Rewards) -> None:
        self.session.add(RewardsModel(id=entity.id, name=entity.name))

    @staticmethod
    def _to_domain(model: RewardsModel) -> Rewards:
        return Rewards(id=model.id, name=model.name)


class SQLAlchemyRewardsReadRepository(RewardsReadRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> RewardsReadModel | None:
        stmt = select(RewardsModel.id, RewardsModel.name).where(RewardsModel.id == id)
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        return RewardsReadModel(id=row.id, name=row.name) if row else None
