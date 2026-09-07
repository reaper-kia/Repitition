from dataclasses import dataclass

from src.modules.client.application.ports.client_repository import ClientReadRepository
from src.modules.client.application.queries.get_client_by_id import GetClientByIdQuery
from src.modules.client.domain.exceptions import ClientNotFoundError


@dataclass
class GetClientByIdQueryHandler:
    client_read_repository: ClientReadRepository

    async def handle(self, query: GetClientByIdQuery):
        result = await self.client_read_repository.get_by_id(query.id)

        if result is None:
            raise ClientNotFoundError(f"Client {query.id} not found")

        return result
