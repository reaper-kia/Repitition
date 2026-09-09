from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ClubReadModel:
    id: UUID
    name: str
    city: str
    manager_user_id: UUID | None
    is_active: bool
