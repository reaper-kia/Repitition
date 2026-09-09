from typing import Protocol
from uuid import UUID

from src.modules.users.application.read_models import UserReadModel
from src.modules.users.domain.entities import User
from src.modules.users.domain.value_objects import Email


class UserRepository(Protocol):
    async def get_by_email(self, email: Email) -> User | None: ...

    async def get_by_id(self, id: UUID) -> User | None: ...

    async def add(self, user: User) -> None: ...


class UserReadRepository(Protocol):
    async def get_by_id(self, id: UUID) -> UserReadModel | None: ...
