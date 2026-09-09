from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ClientReadModel:
    id: UUID
    name: str
