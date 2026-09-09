from dataclasses import dataclass

from src.modules.client.application.queries.list_clients import (
    ListClientsByClubQuery,
)
from src.modules.client.application.read_models import ClientPageReadModel
from src.modules.client.domain.exceptions import AccessDeniedError
from src.modules.users.domain.enums import Role
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class ListClientsByClubHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(
        self,
        query: ListClientsByClubQuery,
    ) -> ClientPageReadModel:
        async with self.uow_factory() as uow:
            if query.actor_role is not Role.NETWORK_ADMIN:
                if query.actor_role is not Role.CLUB_MANAGER:
                    raise AccessDeniedError(
                        "You do not have permission to view " "clients of this club"
                    )

                club_scope = await uow.club_snapshots.get_scope(query.club_id)

                if (
                    club_scope is None
                    or club_scope.manager_user_id != query.actor_user_id
                ):
                    raise AccessDeniedError(
                        "You do not have permission to view " "clients of this club"
                    )

            offset = (query.page - 1) * query.page_size

            return await uow.clients_read.list_by_club(
                club_id=query.club_id,
                limit=query.page_size,
                offset=offset,
            )
