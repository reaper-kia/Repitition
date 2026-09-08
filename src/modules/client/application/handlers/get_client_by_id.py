from uuid import UUID

from src.modules.client.application.queries.get_client_by_id import GetClientByIdQuery, GetClientByUserIdQuery
from src.modules.client.application.read_models import ClientReadModel
from src.modules.client.domain.exceptions import ClientNotFoundError, AccessDeniedError
from src.shared.application.unit_of_work import UnitOfWork

class GetClientByIdHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, query: GetClientByIdQuery) -> ClientReadModel:
        async with self._uow as uow:
            client = await uow.clients_read.get_by_id(query.client_id)
            if not client:
                raise ClientNotFoundError("Client not found")

            # Проверка скоупа доступа (ТЗ 2.5)
            await self._ensure_access(uow, client.club_id, client.user_id, query.actor_user_id, query.is_network_admin)

            return client

class GetClientByUserIdHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, query: GetClientByUserIdQuery) -> ClientReadModel:
        async with self._uow as uow:
            client = await uow.clients_read.get_by_user_id(query.user_id)
            if not client:
                raise ClientNotFoundError("Client not found")

            # Клиент может смотреть только себя (или админ)
            await self._ensure_access(uow, client.club_id, client.user_id, query.actor_user_id, query.is_network_admin)

            return client

    async def _ensure_access(self, uow, club_id: UUID, target_user_id: UUID, actor_user_id: UUID, is_network_admin: bool):
        if is_network_admin:
            return
        if target_user_id == actor_user_id:
            return
        
        # Если не админ и не сам клиент -> проверяем, является ли он менеджером этого клуба
        club_scope = await uow.club_snapshots.get_scope(club_id)
        if not club_scope or actor_user_id not in club_scope.manager_user_ids:
            raise AccessDeniedError("You do not have permission to view this client")