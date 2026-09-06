from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.visit.application.ports.visit_repository import (
    VisitReadRepository,
    VisitRepository,
)
from src.modules.visit.application.read_models import VisitReadModel
from src.modules.visit.domain.entities import Visit
from src.modules.visit.infra.models import VisitModel


class SQLAlchemyVisitRepository(VisitRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Visit | None:
        stmt = select(VisitModel).where(VisitModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def add(self, entity: Visit) -> None:
        self.session.add(VisitModel(id=entity.id, name=entity.name))

    @staticmethod
    def _to_domain(model: VisitModel) -> Visit:
        return Visit(id=model.id, name=model.name)


class SQLAlchemyVisitReadRepository(VisitReadRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> VisitReadModel | None:
        stmt = select(VisitModel.id, VisitModel.name).where(VisitModel.id == id)
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        return VisitReadModel(id=row.id, name=row.name) if row else None
