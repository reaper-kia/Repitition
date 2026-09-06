from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.modules.users.domain.value_objects import Email, UserName


@dataclass
class User:
    name: UserName
    email: Email
    password_hash: str
    is_admin: bool = False
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def register(
        cls,
        name: UserName,
        email: Email,
        password_hash: str,
        is_admin: bool = False,
    ) -> "User":
        return cls(
            name=name,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin,
        )
