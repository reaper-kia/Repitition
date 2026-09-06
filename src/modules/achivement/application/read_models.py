from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AchivementReadModel:
    id: UUID
    name: str
