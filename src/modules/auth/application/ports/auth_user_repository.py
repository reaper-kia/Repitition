from typing import Protocol

from src.modules.auth.application.read_models import AuthUserReadModel


class AuthUserRepository(Protocol):
    async def get_by_email(self, email: str) -> AuthUserReadModel | None: ...
