from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ClubReadModel:
    id: UUID
    name: str
