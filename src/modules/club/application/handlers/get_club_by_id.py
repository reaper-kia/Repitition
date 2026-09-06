from dataclasses import dataclass

from src.modules.club.application.ports.club_repository import ClubReadRepository
from src.modules.club.application.queries.get_club_by_id import GetClubByIdQuery
from src.modules.club.domain.exceptions import ClubNotFoundError


@dataclass
class GetClubByIdQueryHandler:
    club_read_repository: ClubReadRepository

    async def handle(self, query: GetClubByIdQuery):
        result = await self.club_read_repository.get_by_id(query.id)

        if result is None:
            raise ClubNotFoundError(f"Club {query.id} not found")

        return result
