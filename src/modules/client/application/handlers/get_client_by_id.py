from dataclasses import dataclass
from uuid import UUID

from src.modules.client.application.queries.get_client_by_id import (
    GetClientByIdQuery,
    GetClientByUserIdQuery,
)
from src.modules.client.application.read_models import ClientReadModel
from src.modules.client.domain.exceptions import (
    AccessDeniedError,
    ClientNotFoundError,
)
from src.modules.users.domain.enums import Role
from src.shared.application.unit_of_work import (
    UnitOfWork,
    UnitOfWorkFactory,
)


async def _ensure_client_access(
    uow: UnitOfWork,
    client: ClientReadModel,
    actor_user_id: UUID,
    actor_role: Role,
) -> None:
    if actor_role is Role.NETWORK_ADMIN:
        return

    if actor_role is Role.CLIENT and client.user_id == actor_user_id:
        return

    if actor_role is Role.CLUB_MANAGER:
        club_scope = await uow.club_snapshots.get_scope(client.club_id)

        if club_scope is not None and club_scope.manager_user_id == actor_user_id:
            return

    raise AccessDeniedError("You do not have permission to view this client")


@dataclass
class GetClientByIdHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(
        self,
        query: GetClientByIdQuery,
    ) -> ClientReadModel:
        async with self.uow_factory() as uow:
            client = await uow.clients_read.get_by_id(query.client_id)

            if client is None:
                raise ClientNotFoundError("Client not found")

            await _ensure_client_access(
                uow=uow,
                client=client,
                actor_user_id=query.actor_user_id,
                actor_role=query.actor_role,
            )

        return client


@dataclass
class GetClientByUserIdHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(
        self,
        query: GetClientByUserIdQuery,
    ) -> ClientReadModel:
        async with self.uow_factory() as uow:
            client = await uow.clients_read.get_by_user_id(query.user_id)

            if client is None:
                raise ClientNotFoundError("Client not found")

            await _ensure_client_access(
                uow=uow,
                client=client,
                actor_user_id=query.actor_user_id,
                actor_role=query.actor_role,
            )

        return client
