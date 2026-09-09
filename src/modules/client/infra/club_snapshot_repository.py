from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.application.ports.club_snapshot_repository import (
    ClubScopeSnapshot,
    ClubSnapshotRepository,
)
from src.modules.club.infra.models import ClubModel


class SQLAlchemyClubSnapshotRepository(ClubSnapshotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_scope(
        self,
        club_id: UUID,
    ) -> ClubScopeSnapshot | None:
        stmt = select(ClubModel).where(ClubModel.id == club_id)
        result = await self._session.execute(stmt)
        club_model = result.scalar_one_or_none()

        if club_model is None:
            return None

        return ClubScopeSnapshot(
            club_id=club_model.id,
            is_active=club_model.is_active,
            manager_user_id=club_model.manager_user_id,
        )
