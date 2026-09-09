from dataclasses import dataclass
from uuid import UUID

from src.modules.users.domain.enums import Role


@dataclass(frozen=True)
class ListClientsByClubQuery:
    club_id: UUID
    actor_user_id: UUID
    actor_role: Role
    page: int = 1
    page_size: int = 20
