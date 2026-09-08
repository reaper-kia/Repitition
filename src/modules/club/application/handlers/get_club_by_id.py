from dataclasses import dataclass
from src.modules.club.domain.entities import Club
from src.modules.club.domain.exceptions import ClubNotFoundError
from src.modules.club.application.ports.club_repository import ClubRepository
from src.modules.club.application.queries.get_club_by_id import GetClubByIdQuery


@dataclass
class GetClubHandler:
    repo: ClubRepository

    async def handle(self, query: GetClubByIdQuery) -> Club:
        club = await self.repo.get_by_id(query.club_id)
        if club is None:
            raise ClubNotFoundError(f"Club {query.club_id} not found")
        return club