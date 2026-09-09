from dataclasses import dataclass

from src.modules.auth.application.commands.login_user import LoginUserCommand
from src.modules.auth.application.exceptions import InvalidCredentialError
from src.modules.auth.application.ports.auth_user_repository import AuthUserRepository
from src.modules.auth.application.ports.token_service import TokenService
from src.modules.users.application.ports.password_hasher import PasswordHasher


@dataclass
class LoginUserCommandHandler:
    auth_user_repository: AuthUserRepository
    password_hasher: PasswordHasher
    token_service: TokenService

    async def handle(self, cmd: LoginUserCommand) -> str:
        user = await self.auth_user_repository.get_by_email(cmd.email.lower().strip())

        if user is None:
            raise InvalidCredentialError("Invalid email or password")

        is_valid_password = self.password_hasher.verify(
            raw_password=cmd.password,
            password_hash=user.password_hash,
        )

        if not is_valid_password:
            raise InvalidCredentialError("Invalid email or password")

        return self.token_service.create_access_token(user.id)
