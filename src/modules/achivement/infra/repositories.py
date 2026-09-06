from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.achivement.application.ports.achivement_repository import (
    AchivementReadRepository,
    AchivementRepository,
)
from src.modules.achivement.application.read_models import AchivementReadModel
from src.modules.achivement.domain.entities import Achivement
from src.modules.achivement.infra.models import AchivementModel


class SQLAlchemyAchivementRepository(AchivementRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Achivement | None:
        stmt = select(AchivementModel).where(AchivementModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def add(self, entity: Achivement) -> None:
        self.session.add(AchivementModel(id=entity.id, name=entity.name))

    @staticmethod
    def _to_domain(model: AchivementModel) -> Achivement:
        return Achivement(id=model.id, name=model.name)


class SQLAlchemyAchivementReadRepository(AchivementReadRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AchivementReadModel | None:
        stmt = select(AchivementModel.id, AchivementModel.name).where(AchivementModel.id == id)
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        return AchivementReadModel(id=row.id, name=row.name) if row else None
