from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.modules.users.application.commands.register_user import RegisterUserCommand
from src.modules.users.application.handlers.get_user_by_id import (
    GetUserByIdQueryHandler,
)
from src.modules.users.application.handlers.register_user import (
    RegisterUserCommandHandler,
)
from src.modules.users.application.queries.get_user_by_id import GetUserByIdQuery
from src.modules.users.application.read_models import UserReadModel
from src.modules.users.domain.entities import User
from src.modules.users.domain.exceptions import (
    EmailAlreadyExistError,
    InvalidEmailError,
    InvalidUserNameError,
    UserNotFoundError,
    WeakPasswordError,
)
from src.modules.users.domain.value_objects import Email, RawPassword, UserName
from tests.fakes import FakeUoW, FakeUoWFactory


USER_ID = UUID("20000000-0000-0000-0000-000000000001")


class Hasher:
    def hash(self, raw_password: str) -> str:
        return f"hashed:{raw_password}"

    def verify(self, raw_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{raw_password}"


@pytest.mark.unit
def test_user_value_objects_normalize_input() -> None:
    assert Email(" USER@Example.COM ").value == "user@example.com"
    assert UserName(" Alice ").value == "Alice"
    assert RawPassword("password123").value == "password123"


@pytest.mark.unit
@pytest.mark.parametrize("value", ["", "invalid"])
def test_email_rejects_invalid_values(value: str) -> None:
    with pytest.raises(InvalidEmailError):
        Email(value)


@pytest.mark.unit
def test_user_name_rejects_blank_value() -> None:
    with pytest.raises(InvalidUserNameError):
        UserName("   ")


@pytest.mark.unit
@pytest.mark.parametrize("password", ["short", "x" * 129])
def test_password_rejects_invalid_length(password: str) -> None:
    with pytest.raises(WeakPasswordError):
        RawPassword(password)


@pytest.mark.unit
def test_user_register_preserves_admin_flag() -> None:
    user = User.register(
        name=UserName("Admin"),
        email=Email("admin@example.com"),
        password_hash="hash",
        is_admin=True,
    )

    assert user.is_admin is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_user_handler_saves_user() -> None:
    users = SimpleNamespace(
        get_by_email=AsyncMock(return_value=None),
        add=AsyncMock(),
    )
    uow = FakeUoW(users=users)
    handler = RegisterUserCommandHandler(FakeUoWFactory(uow), Hasher())

    user = await handler.handle(
        RegisterUserCommand(
            name=" Alice ",
            email="ALICE@example.com",
            password="password123",
        )
    )

    assert user.name.value == "Alice"
    assert user.email.value == "alice@example.com"
    assert user.password_hash == "hashed:password123"
    users.add.assert_awaited_once_with(user)
    uow.commit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_user_handler_rejects_duplicate_email() -> None:
    users = SimpleNamespace(
        get_by_email=AsyncMock(return_value=object()),
        add=AsyncMock(),
    )
    uow = FakeUoW(users=users)
    handler = RegisterUserCommandHandler(FakeUoWFactory(uow), Hasher())

    with pytest.raises(EmailAlreadyExistError):
        await handler.handle(
            RegisterUserCommand(
                name="Alice",
                email="alice@example.com",
                password="password123",
            )
        )

    users.add.assert_not_awaited()
    uow.commit.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_handler_returns_read_model() -> None:
    model = UserReadModel(
        id=USER_ID,
        name="Alice",
        email="alice@example.com",
        is_admin=False,
    )
    repo = SimpleNamespace(get_by_id=AsyncMock(return_value=model))
    handler = GetUserByIdQueryHandler(repo)

    assert await handler.handle(GetUserByIdQuery(USER_ID)) == model


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_handler_raises_not_found() -> None:
    repo = SimpleNamespace(get_by_id=AsyncMock(return_value=None))
    handler = GetUserByIdQueryHandler(repo)

    with pytest.raises(UserNotFoundError):
        await handler.handle(GetUserByIdQuery(USER_ID))
