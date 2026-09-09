from typing import Protocol
from uuid import UUID

from src.modules.client.application.read_models import (
    ClientPageReadModel,
    ClientReadModel,
)


class ClientReadRepository(Protocol):
    """Порт для чтения Client read models."""

    async def get_by_id(
        self,
        client_id: UUID,
    ) -> ClientReadModel | None: ...

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> ClientReadModel | None: ...

    async def list_by_club(
        self,
        club_id: UUID,
        limit: int,
        offset: int,
    ) -> ClientPageReadModel: ...
