from abc import ABC, abstractmethod
from uuid import UUID
from src.modules.club.domain.entities import Club


class ClubRepository(ABC):
    @abstractmethod
    async def add(self, club: Club) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, club_id: UUID) -> Club | None:
        pass

    @abstractmethod
    async def save(self, club: Club) -> None:
        pass
