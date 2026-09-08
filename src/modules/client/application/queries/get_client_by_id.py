from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class GetClientByIdQuery:
    client_id: UUID

@dataclass(frozen=True)
class GetClientByUserIdQuery:
    user_id: UUID