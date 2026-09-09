from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.visit.application.ports.client_snapshot_repository import (
    ClientSnapshot,
    ClientSnapshotRepository,
)
# Импортируем ORM-модель из модуля Client (так как они в одной БД)
from src.modules.client.infra.models import ClientModel


class SQLAlchemyClientSnapshotRepository(ClientSnapshotRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, client_id: UUID) -> ClientSnapshot | None:
        stmt = select(ClientModel).where(ClientModel.id == client_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return ClientSnapshot(
            client_id=model.id,
            club_id=model.club_id,
            # Проверяем, что абонемент активен (статус хранится как строка)
            is_active=(model.status == "ACTIVE"), 
        )