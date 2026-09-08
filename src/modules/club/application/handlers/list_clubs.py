from dataclasses import dataclass
from src.modules.club.application.ports.club_read_repository import ClubReadRepository, ClubScope
from src.modules.club.application.queries.list_clubs import ListClubsQuery


@dataclass
class ListClubsHandler:
    read_repo: ClubReadRepository

    async def handle(self, query: ListClubsQuery) -> list[ClubScope]:
        return await self.read_repo.list_all()