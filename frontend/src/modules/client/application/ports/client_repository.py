from typing import Protocol
from uuid import UUID

from src.modules.client.application.read_models import ClientReadModel
from src.modules.client.domain.entities import Client


class ClientRepository(Protocol):
    async def get_by_id(self, id: UUID) -> Client | None: ...

    async def add(self, entity: Client) -> None: ...


class ClientReadRepository(Protocol):
    async def get_by_id(self, id: UUID) -> ClientReadModel | None: ...
