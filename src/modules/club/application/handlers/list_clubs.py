from dataclasses import dataclass

from src.modules.club.application.queries.list_clubs import ListClubsQuery
from src.modules.club.application.read_models import ClubReadModel
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class ListClubsHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, query: ListClubsQuery) -> list[ClubReadModel]:
        async with self.uow_factory() as uow:
            return await uow.clubs_read.list_all()
