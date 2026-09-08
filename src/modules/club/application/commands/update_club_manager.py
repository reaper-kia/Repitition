from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UpdateClubManagerCommand:
    club_id: UUID
    manager_user_id: UUID