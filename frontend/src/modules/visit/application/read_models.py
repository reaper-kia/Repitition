from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class VisitReadModel:
    id: UUID
    name: str
