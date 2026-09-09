from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from src.modules.club.application.read_models import ClubReadModel


@dataclass(frozen=True)
class ClubScope:
    club_id: UUID
    is_active: bool
    manager_user_id: UUID | None


class ClubReadRepository(Protocol):
    async def get_scope(self, club_id: UUID) -> ClubScope | None: ...

    async def list_all(self) -> list[ClubReadModel]: ...

    async def get_by_manager(self, user_id: UUID) -> ClubScope | None: ...
