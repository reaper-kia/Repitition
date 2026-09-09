from dataclasses import dataclass

from src.modules.club.application.queries.get_club_by_id import GetClubByIdQuery
from src.modules.club.domain.entities import Club
from src.modules.club.domain.exceptions import ClubNotFoundError
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class GetClubHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, query: GetClubByIdQuery) -> Club:
        async with self.uow_factory() as uow:
            club = await uow.clubs.get_by_id(query.id)

            if club is None:
                raise ClubNotFoundError(f"Club {query.id} not found")

        return club
