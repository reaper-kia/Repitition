from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import Response

from src.modules.auth.api.cookies import (
    delete_access_token_cookie,
    set_access_token_cookie,
)
from src.modules.auth.application.commands.login_user import LoginUserCommand
from src.modules.auth.application.exceptions import InvalidCredentialError
from src.modules.auth.application.handlers.login_user import LoginUserCommandHandler
from src.modules.auth.application.read_models import AuthUserReadModel


USER_ID = UUID("30000000-0000-0000-0000-000000000001")


class AuthRepository:
    def __init__(self, user):
        self.user = user
        self.requested_email = None

    async def get_by_email(self, email: str):
        self.requested_email = email
        return self.user


class Hasher:
    def __init__(self, valid: bool):
        self.valid = valid

    def verify(self, raw_password: str, password_hash: str) -> bool:
        return self.valid


class TokenService:
    def create_access_token(self, user_id: UUID) -> str:
        return f"token:{user_id}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_handler_normalizes_email_and_returns_token() -> None:
    user = AuthUserReadModel(
        id=USER_ID,
        email="user@example.com",
        password_hash="hash",
    )
    repo = AuthRepository(user)
    handler = LoginUserCommandHandler(repo, Hasher(True), TokenService())

    token = await handler.handle(LoginUserCommand(" USER@example.com ", "password123"))

    assert repo.requested_email == "user@example.com"
    assert token == f"token:{USER_ID}"


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user", "valid_password"),
    [(None, True), (SimpleNamespace(password_hash="hash"), False)],
)
async def test_login_handler_rejects_invalid_credentials(
    user,
    valid_password: bool,
) -> None:
    handler = LoginUserCommandHandler(
        AuthRepository(user),
        Hasher(valid_password),
        TokenService(),
    )

    with pytest.raises(InvalidCredentialError):
        await handler.handle(LoginUserCommand("user@example.com", "bad-password"))


@pytest.mark.unit
def test_access_cookie_is_http_only() -> None:
    response = Response()

    set_access_token_cookie(response, "secret-token")

    header = response.headers["set-cookie"]
    assert "access_token=secret-token" in header
    assert "HttpOnly" in header


@pytest.mark.unit
def test_logout_cookie_is_deleted() -> None:
    response = Response()

    delete_access_token_cookie(response)

    header = response.headers["set-cookie"]
    assert "access_token=" in header
    assert "Max-Age=0" in header
