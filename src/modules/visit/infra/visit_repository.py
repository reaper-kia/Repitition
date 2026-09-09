from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.visit.application.ports.visit_repository import VisitRepository
from src.modules.visit.domain.entities import Visit
from src.modules.visit.infra.models import VisitModel


class SQLAlchemyVisitRepository(VisitRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, visit: Visit) -> None:
        model = self._to_model(visit)
        self._session.add(model)
        # commit() НЕ вызываем! Ждем UoW.

    async def get_by_external_id(self, external_id: str) -> Visit | None:
        """Найти визит по external_id (для проверки идемпотентности и закрытия)."""
        stmt = select(VisitModel).where(VisitModel.external_id == external_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    # --- Мапперы ---
    @staticmethod
    def _to_model(visit: Visit) -> VisitModel:
        return VisitModel(
            id=visit.id,
            external_id=visit.external_id,
            client_id=visit.client_id,
            club_id=visit.club_id,
            entered_at=visit.entered_at,
            exited_at=visit.exited_at,
        )

    @staticmethod
    def _to_domain(model: VisitModel) -> Visit:
        return Visit(
            id=model.id,
            external_id=model.external_id,
            client_id=model.client_id,
            club_id=model.club_id,
            entered_at=model.entered_at,
            exited_at=model.exited_at,
        )