from dataclasses import dataclass
from uuid import UUID

from src.modules.users.domain.enums import Role


@dataclass(frozen=True)
class GetClientByIdQuery:
    client_id: UUID
    actor_user_id: UUID
    actor_role: Role


@dataclass(frozen=True)
class GetClientByUserIdQuery:
    user_id: UUID
    actor_user_id: UUID
    actor_role: Role
