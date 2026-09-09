# src/modules/visit/infra/repositories/visit_read_repository.py
from uuid import UUID
from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.visit.application.ports.visit_read_repository import VisitReadRepository
from src.modules.visit.application.read_models import VisitReadModel
from src.modules.visit.infra.models import VisitModel


class SQLAlchemyVisitReadRepository(VisitReadRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_current_by_club(self, club_id: UUID) -> List[VisitReadModel]:
        """Получить все открытые визиты в клубе (где exited_at IS NULL)."""
        stmt = (
            select(VisitModel)
            .where(
                VisitModel.club_id == club_id,
                VisitModel.exited_at.is_(None)
            )
            .order_by(VisitModel.entered_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_read_model(m) for m in models]

    async def get_history_by_client(
        self, client_id: UUID, limit: int, offset: int
    ) -> Tuple[List[VisitReadModel], int]:
        """Получить историю визитов клиента с пагинацией. Возвращает (items, total)."""
        # Считаем общее количество
        count_stmt = select(func.count()).select_from(VisitModel).where(VisitModel.client_id == client_id)
        total = await self._session.scalar(count_stmt)

        # Берем страницу
        stmt = (
            select(VisitModel)
            .where(VisitModel.client_id == client_id)
            .order_by(VisitModel.entered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        items = [self._to_read_model(m) for m in models]
        return items, total

    @staticmethod
    def _to_read_model(model: VisitModel) -> VisitReadModel:
        return VisitReadModel(
            id=model.id,
            external_id=model.external_id,
            client_id=model.client_id,
            club_id=model.club_id,
            entered_at=model.entered_at,
            exited_at=model.exited_at,
        )