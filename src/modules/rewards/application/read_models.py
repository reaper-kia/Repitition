from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RewardsReadModel:
    id: UUID
    name: str
