from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.club.application.commands.create_club import CreateClubCommand
from src.modules.club.application.commands.update_club_manager import (
    UpdateClubManagerCommand,
)
from src.modules.club.application.handlers.create_club import CreateClubHandler
from src.modules.club.application.handlers.get_club_by_id import GetClubHandler
from src.modules.club.application.handlers.list_clubs import ListClubsHandler
from src.modules.club.application.handlers.update_club_manager import (
    UpdateClubManagerHandler,
)
from src.modules.club.application.queries.get_club_by_id import GetClubByIdQuery
from src.modules.club.application.queries.list_clubs import ListClubsQuery
from src.modules.club.application.read_models import ClubReadModel
from src.modules.club.domain.entities import Club
from src.modules.club.domain.exceptions import (
    ClubNotFoundError,
    ManagerUserNotClubManagerError,
    ManagerUserNotFoundError,
)
from src.modules.club.domain.value_objects import City, ClubName
from src.modules.users.domain.enums import Role


class FakeClubRepository:
    def __init__(self) -> None:
        self.clubs: dict = {}

    async def add(self, club: Club) -> None:
        self.clubs[club.id] = club

    async def get_by_id(self, club_id):
        return self.clubs.get(club_id)

    async def save(self, club: Club) -> None:
        self.clubs[club.id] = club


class FakeClubReadRepository:
    def __init__(
        self,
        clubs: list[ClubReadModel] | None = None,
    ) -> None:
        self.clubs = clubs or []

    async def list_all(self) -> list[ClubReadModel]:
        return self.clubs


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.users = AsyncMock()
        self.clubs = FakeClubRepository()
        self.clubs_read = FakeClubReadRepository()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is not None:
            await self.rollback()


class FakeUnitOfWorkFactory:
    def __init__(self, uow: FakeUnitOfWork) -> None:
        self.uow = uow
        self.calls = 0

    def __call__(self) -> FakeUnitOfWork:
        self.calls += 1
        return self.uow


@pytest.mark.asyncio
async def test_create_club_uses_factory_and_commits() -> None:
    uow = FakeUnitOfWork()
    factory = FakeUnitOfWorkFactory(uow)
    manager_id = uuid4()
    uow.users.get_by_id.return_value = SimpleNamespace(role=Role.CLUB_MANAGER)
    handler = CreateClubHandler(factory)

    club = await handler.handle(
        CreateClubCommand(
            name=" Test Club ",
            city=" Moscow ",
            manager_user_id=manager_id,
        )
    )

    assert factory.calls == 1
    assert club.name.value == "Test Club"
    assert club.city.value == "Moscow"
    assert club.manager_user_id == manager_id
    assert await uow.clubs.get_by_id(club.id) is club
    uow.users.get_by_id.assert_awaited_once_with(manager_id)
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_club_rejects_missing_manager() -> None:
    uow = FakeUnitOfWork()
    uow.users.get_by_id.return_value = None
    handler = CreateClubHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(ManagerUserNotFoundError):
        await handler.handle(
            CreateClubCommand(
                name="Club",
                city="City",
                manager_user_id=uuid4(),
            )
        )

    uow.commit.assert_not_awaited()
    uow.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_club_rejects_wrong_manager_role() -> None:
    uow = FakeUnitOfWork()
    uow.users.get_by_id.return_value = SimpleNamespace(role=Role.CLIENT)
    handler = CreateClubHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(ManagerUserNotClubManagerError):
        await handler.handle(
            CreateClubCommand(
                name="Club",
                city="City",
                manager_user_id=uuid4(),
            )
        )

    uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_manager_uses_uow_users_and_commits() -> None:
    uow = FakeUnitOfWork()
    factory = FakeUnitOfWorkFactory(uow)
    club = Club.create(ClubName("Club"), City("City"))
    await uow.clubs.add(club)

    manager_id = uuid4()
    uow.users.get_by_id.return_value = SimpleNamespace(role=Role.CLUB_MANAGER)
    handler = UpdateClubManagerHandler(factory)

    result = await handler.handle(
        UpdateClubManagerCommand(
            club_id=club.id,
            manager_user_id=manager_id,
        )
    )

    assert factory.calls == 1
    assert result.manager_user_id == manager_id
    uow.users.get_by_id.assert_awaited_once_with(manager_id)
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_manager_rejects_missing_club() -> None:
    uow = FakeUnitOfWork()
    handler = UpdateClubManagerHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(ClubNotFoundError):
        await handler.handle(
            UpdateClubManagerCommand(
                club_id=uuid4(),
                manager_user_id=uuid4(),
            )
        )

    uow.users.get_by_id.assert_not_awaited()
    uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_club_uses_factory() -> None:
    uow = FakeUnitOfWork()
    factory = FakeUnitOfWorkFactory(uow)
    club = Club.create(ClubName("Club"), City("City"))
    await uow.clubs.add(club)
    handler = GetClubHandler(factory)

    result = await handler.handle(GetClubByIdQuery(id=club.id))

    assert result is club
    assert factory.calls == 1
    uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_club_raises_when_missing() -> None:
    uow = FakeUnitOfWork()
    handler = GetClubHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(ClubNotFoundError):
        await handler.handle(GetClubByIdQuery(id=uuid4()))


@pytest.mark.asyncio
async def test_list_clubs_uses_read_repository_from_uow() -> None:
    uow = FakeUnitOfWork()
    factory = FakeUnitOfWorkFactory(uow)
    expected = [
        ClubReadModel(
            id=uuid4(),
            name="Club",
            city="City",
            manager_user_id=None,
            is_active=True,
        )
    ]
    uow.clubs_read = FakeClubReadRepository(expected)
    handler = ListClubsHandler(factory)

    result = await handler.handle(ListClubsQuery())

    assert result == expected
    assert factory.calls == 1
    uow.commit.assert_not_awaited()
