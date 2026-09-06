from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.club.application.ports.club_repository import (
    ClubReadRepository,
    ClubRepository,
)
from src.modules.club.application.read_models import ClubReadModel
from src.modules.club.domain.entities import Club
from src.modules.club.infra.models import ClubModel


class SQLAlchemyClubRepository(ClubRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Club | None:
        stmt = select(ClubModel).where(ClubModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def add(self, entity: Club) -> None:
        self.session.add(ClubModel(id=entity.id, name=entity.name))

    @staticmethod
    def _to_domain(model: ClubModel) -> Club:
        return Club(id=model.id, name=model.name)


class SQLAlchemyClubReadRepository(ClubReadRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> ClubReadModel | None:
        stmt = select(ClubModel.id, ClubModel.name).where(ClubModel.id == id)
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        return ClubReadModel(id=row.id, name=row.name) if row else None
