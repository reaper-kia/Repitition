import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.modules.club.application.commands.create_club import CreateClubCommand
from src.modules.club.application.commands.update_club_manager import UpdateClubManagerCommand
from src.modules.club.application.queries.get_club import GetClubQuery
from src.modules.club.application.queries.list_clubs import ListClubsQuery
from src.modules.club.application.handlers.create_club import CreateClubHandler
from src.modules.club.application.handlers.update_club_manager import UpdateClubManagerHandler
from src.modules.club.application.handlers.get_club import GetClubHandler
from src.modules.club.application.handlers.list_clubs import ListClubsHandler
from src.modules.club.domain.entities import Club
from src.modules.club.domain.value_objects import ClubName, City
from src.modules.club.domain.exceptions import (
    ClubNotFoundError,
    ManagerUserNotFoundError,
    ManagerUserNotClubManagerError,
)


# ---------- Fake repositories ----------
class FakeClubRepository:
    def __init__(self):
        self._clubs = {}

    async def add(self, club: Club):
        self._clubs[club.id] = club

    async def get_by_id(self, club_id):
        return self._clubs.get(club_id)

    async def save(self, club: Club):
        self._clubs[club.id] = club


class FakeClubReadRepository:
    def __init__(self, clubs=None):
        self._clubs = clubs or {}

    async def get_scope(self, club_id):
        from src.modules.club.application.ports.club_read_repository import ClubScope
        club = self._clubs.get(club_id)
        if club is None:
            return None
        return ClubScope(
            club_id=club.id,
            is_active=club.is_active,
            manager_user_id=club.manager_user_id,
        )

    async def list_all_full(self):
        return list(self._clubs.values())

    async def get_by_manager(self, user_id):
        from src.modules.club.application.ports.club_read_repository import ClubScope
        for club in self._clubs.values():
            if club.manager_user_id == user_id:
                return ClubScope(
                    club_id=club.id,
                    is_active=club.is_active,
                    manager_user_id=club.manager_user_id,
                )
        return None


# ---------- Fake Unit of Work ----------
class FakeUnitOfWork:
    def __init__(self):
        self.clubs = FakeClubRepository()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


# ---------- Fixtures ----------
@pytest.fixture
def fake_uow():
    return FakeUnitOfWork()


@pytest.fixture
def fake_user_repo():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def create_club_handler(fake_uow, fake_user_repo):
    return CreateClubHandler(fake_uow, fake_user_repo)


@pytest.fixture
def update_manager_handler(fake_uow, fake_user_repo):
    return UpdateClubManagerHandler(fake_uow, fake_user_repo)


@pytest.fixture
def get_club_handler():
    repo = FakeClubRepository()
    return GetClubHandler(repo)


@pytest.fixture
def list_clubs_handler():
    read_repo = FakeClubReadRepository()
    return ListClubsHandler(read_repo)


# ---------- Tests ----------
@pytest.mark.asyncio
async def test_create_club_success(create_club_handler, fake_uow, fake_user_repo):
    user_id = uuid4()
    user = MagicMock()
    user.is_club_manager = True
    fake_user_repo.get_by_id.return_value = user

    cmd = CreateClubCommand(
        name="Test Club",
        city="Moscow",
        manager_user_id=user_id,
    )

    club = await create_club_handler.handle(cmd)

    assert club.name.value == "Test Club"
    assert club.city.value == "Moscow"
    assert club.manager_user_id == user_id
    assert club.is_active is True
    assert fake_uow.committed is True
    fake_user_repo.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_create_club_manager_not_found(create_club_handler, fake_user_repo):
    fake_user_repo.get_by_id.return_value = None

    cmd = CreateClubCommand(
        name="Test Club",
        city="Moscow",
        manager_user_id=uuid4(),
    )

    with pytest.raises(ManagerUserNotFoundError):
        await create_club_handler.handle(cmd)


@pytest.mark.asyncio
async def test_create_club_manager_not_club_manager(create_club_handler, fake_user_repo):
    user_id = uuid4()
    user = MagicMock()
    user.is_club_manager = False
    fake_user_repo.get_by_id.return_value = user

    cmd = CreateClubCommand(
        name="Test Club",
        city="Moscow",
        manager_user_id=user_id,
    )

    with pytest.raises(ManagerUserNotClubManagerError):
        await create_club_handler.handle(cmd)


@pytest.mark.asyncio
async def test_update_manager_success(update_manager_handler, fake_uow, fake_user_repo):
    club = Club.create(
        name=ClubName("Test Club"),
        city=City("Moscow"),
        manager_user_id=None,
    )
    await fake_uow.clubs.add(club)

    user_id = uuid4()
    user = MagicMock()
    user.is_club_manager = True
    fake_user_repo.get_by_id.return_value = user

    cmd = UpdateClubManagerCommand(
        club_id=club.id,
        manager_user_id=user_id,
    )

    updated_club = await update_manager_handler.handle(cmd)

    assert updated_club.manager_user_id == user_id
    assert fake_uow.committed is True


@pytest.mark.asyncio
async def test_update_manager_club_not_found(update_manager_handler, fake_uow, fake_user_repo):
    cmd = UpdateClubManagerCommand(
        club_id=uuid4(),
        manager_user_id=uuid4(),
    )

    with pytest.raises(ClubNotFoundError):
        await update_manager_handler.handle(cmd)


@pytest.mark.asyncio
async def test_get_club_success():
    repo = FakeClubRepository()
    club = Club.create(
        name=ClubName("Test Club"),
        city=City("Moscow"),
        manager_user_id=None,
    )
    await repo.add(club)

    handler = GetClubHandler(repo)
    query = GetClubQuery(club_id=club.id)
    found = await handler.handle(query)

    assert found.id == club.id
    assert found.name.value == "Test Club"


@pytest.mark.asyncio
async def test_get_club_not_found():
    repo = FakeClubRepository()
    handler = GetClubHandler(repo)
    query = GetClubQuery(club_id=uuid4())

    with pytest.raises(ClubNotFoundError):
        await handler.handle(query)


@pytest.mark.asyncio
async def test_list_clubs():
    read_repo = FakeClubReadRepository()
    club1 = Club.create(
        name=ClubName("Club 1"),
        city=City("City 1"),
        manager_user_id=None,
    )
    club2 = Club.create(
        name=ClubName("Club 2"),
        city=City("City 2"),
        manager_user_id=None,
    )
    read_repo._clubs = {club1.id: club1, club2.id: club2}

    handler = ListClubsHandler(read_repo)
    query = ListClubsQuery()
    clubs = await handler.handle(query)

    assert len(clubs) == 2
    assert any(c.name.value == "Club 1" for c in clubs)
    assert any(c.name.value == "Club 2" for c in clubs)