from abc import ABC, abstractmethod
from uuid import UUID
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ClubScope:
    club_id: UUID
    is_active: bool
    manager_user_id: UUID | None


class ClubReadRepository(ABC):
    @abstractmethod
    async def get_scope(self, club_id: UUID) -> ClubScope | None:
        pass

    @abstractmethod
    async def list_all(self) -> List[ClubScope]:
        pass

    @abstractmethod
    async def get_by_manager(self, user_id: UUID) -> ClubScope | None:
        pass