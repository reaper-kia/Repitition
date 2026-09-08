from src.modules.client.application.queries.list_clients import ListClientsByClubQuery
from src.modules.client.application.read_models import ClientPageReadModel
from src.modules.client.domain.exceptions import AccessDeniedError
from src.shared.application.unit_of_work import UnitOfWork

class ListClientsByClubHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, query: ListClientsByClubQuery) -> ClientPageReadModel:
        async with self._uow as uow:
            # Проверка скоупа: NETWORK_ADMIN может всё, CLUB_MANAGER только свой клуб
            if not query.is_network_admin:
                club_scope = await uow.club_snapshots.get_scope(query.club_id)
                if not club_scope or query.actor_user_id not in club_scope.manager_user_ids:
                    raise AccessDeniedError("You do not have permission to view clients of this club")

            offset = (query.page - 1) * query.page_size
            return await uow.clients_read.list_by_club(
                club_id=query.club_id, 
                limit=query.page_size, 
                offset=offset
            )