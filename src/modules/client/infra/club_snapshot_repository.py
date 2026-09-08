from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.application.ports.club_snapshot_repository import (
    ClubScopeSnapshot,
    ClubSnapshotRepository,
)
from src.modules.club.infra.models import ClubModel 


class SQLAlchemyClubSnapshotRepository(ClubSnapshotRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_scope(self, club_id: UUID) -> ClubScopeSnapshot | None:
        """
        Делает 'слепок' с клуба для проверки прав и активности.
        Мы не импортируем домен Club, а просто читаем нужные поля из БД.
        """
        stmt = select(ClubModel).where(ClubModel.id == club_id)
        result = await self._session.execute(stmt)
        club_model = result.scalar_one_or_none()

        if not club_model:
            return None

        manager_ids = [club_model.manager_user_id] if club_model.manager_user_id else []

        return ClubScopeSnapshot(
            club_id=club_model.id,
            is_active=club_model.is_active,
            manager_user_ids=manager_ids,
        )