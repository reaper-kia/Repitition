from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateClubCommand:
    name: str
    city: str
    manager_user_id: UUID | None = None