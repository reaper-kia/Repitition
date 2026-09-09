from uuid import UUID, uuid4

import pytest
from unittest.mock import AsyncMock

from src.modules.client.application.commands.create_client import (
    CreateClientCommand,
)
from src.modules.client.application.handlers.create_client import (
    CreateClientHandler,
)
from src.modules.client.application.handlers.get_client_by_id import (
    GetClientByIdHandler,
    GetClientByUserIdHandler,
)
from src.modules.client.application.handlers.list_clients import (
    ListClientsByClubHandler,
)
from src.modules.client.application.ports.club_snapshot_repository import (
    ClubScopeSnapshot,
)
from src.modules.client.application.queries.get_client_by_id import (
    GetClientByIdQuery,
    GetClientByUserIdQuery,
)
from src.modules.client.application.queries.list_clients import (
    ListClientsByClubQuery,
)
from src.modules.client.application.read_models import (
    ClientPageReadModel,
    ClientReadModel,
)
from src.modules.client.domain.entities import Client
from src.modules.client.domain.enums import MembershipType
from src.modules.client.domain.exceptions import (
    AccessDeniedError,
    ClientAlreadyExistsError,
    ClientNotFoundError,
    ClubInactiveError,
    InvalidReferralCodeError,
    ReferralCodeGenerationError,
)
from src.modules.client.domain.value_objects import Membership, ReferralCode
from src.modules.users.domain.enums import Role


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeClientRepository:
    def __init__(self, clients: list[Client] | None = None) -> None:
        self._by_id: dict[UUID, Client] = {c.id: c for c in (clients or [])}

    async def add(self, client: Client) -> None:
        self._by_id[client.id] = client

    async def get_by_id(self, client_id: UUID) -> Client | None:
        return self._by_id.get(client_id)

    async def get_by_user_id(self, user_id: UUID) -> Client | None:
        return next((c for c in self._by_id.values() if c.user_id == user_id), None)

    async def get_by_referral_code(self, code: str) -> Client | None:
        return next(
            (c for c in self._by_id.values() if c.referral_code.value == code),
            None,
        )


class AlwaysCollidingClientRepository(FakeClientRepository):
    """Имитирует ситуацию, когда каждый сгенерированный код уже занят."""

    async def get_by_referral_code(self, code: str) -> Client | None:
        return object()  # truthy — коллизия всегда есть


class FakeClientReadRepository:
    def __init__(
        self,
        *,
        by_id: dict[UUID, ClientReadModel] | None = None,
        by_user_id: dict[UUID, ClientReadModel] | None = None,
        page: ClientPageReadModel | None = None,
    ) -> None:
        self._by_id = by_id or {}
        self._by_user_id = by_user_id or {}
        self._page = page or ClientPageReadModel(items=[], total=0)

    async def get_by_id(self, client_id: UUID) -> ClientReadModel | None:
        return self._by_id.get(client_id)

    async def get_by_user_id(self, user_id: UUID) -> ClientReadModel | None:
        return self._by_user_id.get(user_id)

    async def list_by_club(
        self, club_id: UUID, limit: int, offset: int
    ) -> ClientPageReadModel:
        return self._page


class FakeClubSnapshotRepository:
    def __init__(self, scope: ClubScopeSnapshot | None = None) -> None:
        self.scope = scope

    async def get_scope(self, club_id: UUID) -> ClubScopeSnapshot | None:
        return self.scope


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        clients: FakeClientRepository | None = None,
        clients_read: FakeClientReadRepository | None = None,
        club_snapshots: FakeClubSnapshotRepository | None = None,
    ) -> None:
        self.clients = clients or FakeClientRepository()
        self.clients_read = clients_read or FakeClientReadRepository()
        self.club_snapshots = club_snapshots or FakeClubSnapshotRepository()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self) -> "FakeUnitOfWork":
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


def _make_client(
    *,
    user_id: UUID | None = None,
    club_id: UUID | None = None,
    referral_code: str = "ABCDEF",
) -> Client:
    return Client.register(
        user_id=user_id or uuid4(),
        club_id=club_id or uuid4(),
        display_name="Existing Client",
        membership=Membership(
            type=MembershipType.ONE_MONTH,
            expires_at=__import__("datetime").datetime(
                2030, 1, 1, tzinfo=__import__("datetime").UTC
            ),
        ),
        referral_code=ReferralCode(referral_code),
    )


# ---------------------------------------------------------------------------
# CreateClientHandler
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_create_client_registers_and_commits() -> None:
    club_id = uuid4()
    uow = FakeUnitOfWork(
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(club_id=club_id, is_active=True, manager_user_id=None)
        )
    )
    factory = FakeUnitOfWorkFactory(uow)
    handler = CreateClientHandler(factory)

    client = await handler.handle(
        CreateClientCommand(
            user_id=uuid4(),
            club_id=club_id,
            display_name="New Client",
            membership_type=MembershipType.THREE_MONTHS,
            referral_code=None,
        )
    )

    assert factory.calls == 1
    assert client.membership.type is MembershipType.THREE_MONTHS
    assert client.referred_by_client_id is None
    assert await uow.clients.get_by_id(client.id) is client
    uow.commit.assert_awaited_once()


@pytest.mark.unit
async def test_create_client_attaches_referrer_when_code_valid() -> None:
    club_id = uuid4()
    referrer = _make_client(club_id=club_id)
    uow = FakeUnitOfWork(
        clients=FakeClientRepository([referrer]),
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(club_id=club_id, is_active=True, manager_user_id=None)
        ),
    )
    handler = CreateClientHandler(FakeUnitOfWorkFactory(uow))

    client = await handler.handle(
        CreateClientCommand(
            user_id=uuid4(),
            club_id=club_id,
            display_name="New Client",
            membership_type=MembershipType.ONE_MONTH,
            referral_code=referrer.referral_code.value,
        )
    )

    assert client.referred_by_client_id == referrer.id


@pytest.mark.unit
async def test_create_client_rejects_inactive_club() -> None:
    club_id = uuid4()
    uow = FakeUnitOfWork(
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(club_id=club_id, is_active=False, manager_user_id=None)
        )
    )
    handler = CreateClientHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(ClubInactiveError):
        await handler.handle(
            CreateClientCommand(
                user_id=uuid4(),
                club_id=club_id,
                display_name="X",
                membership_type=MembershipType.ONE_MONTH,
                referral_code=None,
            )
        )

    uow.commit.assert_not_awaited()


@pytest.mark.unit
async def test_create_client_rejects_duplicate_user() -> None:
    club_id = uuid4()
    user_id = uuid4()
    existing = _make_client(user_id=user_id, club_id=club_id)
    uow = FakeUnitOfWork(
        clients=FakeClientRepository([existing]),
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(club_id=club_id, is_active=True, manager_user_id=None)
        ),
    )
    handler = CreateClientHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(ClientAlreadyExistsError):
        await handler.handle(
            CreateClientCommand(
                user_id=user_id,
                club_id=club_id,
                display_name="X",
                membership_type=MembershipType.ONE_MONTH,
                referral_code=None,
            )
        )


@pytest.mark.unit
async def test_create_client_rejects_unknown_referral_code() -> None:
    club_id = uuid4()
    uow = FakeUnitOfWork(
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(club_id=club_id, is_active=True, manager_user_id=None)
        )
    )
    handler = CreateClientHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(InvalidReferralCodeError):
        await handler.handle(
            CreateClientCommand(
                user_id=uuid4(),
                club_id=club_id,
                display_name="X",
                membership_type=MembershipType.ONE_MONTH,
                referral_code="ZZZZZZ",
            )
        )


@pytest.mark.unit
async def test_create_client_gives_up_after_five_colliding_codes() -> None:
    club_id = uuid4()
    uow = FakeUnitOfWork(
        clients=AlwaysCollidingClientRepository(),
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(club_id=club_id, is_active=True, manager_user_id=None)
        ),
    )
    handler = CreateClientHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(ReferralCodeGenerationError):
        await handler.handle(
            CreateClientCommand(
                user_id=uuid4(),
                club_id=club_id,
                display_name="X",
                membership_type=MembershipType.ONE_MONTH,
                referral_code=None,
            )
        )

    uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# GetClientByIdHandler / GetClientByUserIdHandler — скоуп доступа
# ---------------------------------------------------------------------------


def _read_model(client_id: UUID, user_id: UUID, club_id: UUID) -> ClientReadModel:
    import datetime as dt

    return ClientReadModel(
        id=client_id,
        user_id=user_id,
        club_id=club_id,
        display_name="Client",
        membership_type=MembershipType.ONE_MONTH,
        membership_expires_at=dt.datetime(2030, 1, 1, tzinfo=dt.UTC),
        referral_code="ABCDEF",
        referred_by_client_id=None,
        acquisition_channel="ORGANIC",
        status="ACTIVE",
        registered_at=dt.datetime(2024, 1, 1, tzinfo=dt.UTC),
    )


@pytest.mark.unit
async def test_get_client_by_id_allows_network_admin() -> None:
    client_id, user_id, club_id = uuid4(), uuid4(), uuid4()
    model = _read_model(client_id, user_id, club_id)
    uow = FakeUnitOfWork(
        clients_read=FakeClientReadRepository(by_id={client_id: model})
    )
    handler = GetClientByIdHandler(FakeUnitOfWorkFactory(uow))

    result = await handler.handle(
        GetClientByIdQuery(
            client_id=client_id, actor_user_id=uuid4(), actor_role=Role.NETWORK_ADMIN
        )
    )

    assert result is model


@pytest.mark.unit
async def test_get_client_by_id_allows_self() -> None:
    client_id, user_id, club_id = uuid4(), uuid4(), uuid4()
    model = _read_model(client_id, user_id, club_id)
    uow = FakeUnitOfWork(
        clients_read=FakeClientReadRepository(by_id={client_id: model})
    )
    handler = GetClientByIdHandler(FakeUnitOfWorkFactory(uow))

    result = await handler.handle(
        GetClientByIdQuery(
            client_id=client_id, actor_user_id=user_id, actor_role=Role.CLIENT
        )
    )

    assert result is model


@pytest.mark.unit
async def test_get_client_by_id_allows_manager_of_same_club() -> None:
    client_id, user_id, club_id = uuid4(), uuid4(), uuid4()
    manager_id = uuid4()
    model = _read_model(client_id, user_id, club_id)
    uow = FakeUnitOfWork(
        clients_read=FakeClientReadRepository(by_id={client_id: model}),
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(
                club_id=club_id, is_active=True, manager_user_id=manager_id
            )
        ),
    )
    handler = GetClientByIdHandler(FakeUnitOfWorkFactory(uow))

    result = await handler.handle(
        GetClientByIdQuery(
            client_id=client_id, actor_user_id=manager_id, actor_role=Role.CLUB_MANAGER
        )
    )

    assert result is model


@pytest.mark.unit
async def test_get_client_by_id_denies_other_client() -> None:
    client_id, user_id, club_id = uuid4(), uuid4(), uuid4()
    model = _read_model(client_id, user_id, club_id)
    uow = FakeUnitOfWork(
        clients_read=FakeClientReadRepository(by_id={client_id: model})
    )
    handler = GetClientByIdHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(AccessDeniedError):
        await handler.handle(
            GetClientByIdQuery(
                client_id=client_id, actor_user_id=uuid4(), actor_role=Role.CLIENT
            )
        )


@pytest.mark.unit
async def test_get_client_by_id_denies_manager_of_other_club() -> None:
    client_id, user_id, club_id = uuid4(), uuid4(), uuid4()
    model = _read_model(client_id, user_id, club_id)
    uow = FakeUnitOfWork(
        clients_read=FakeClientReadRepository(by_id={client_id: model}),
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(club_id=club_id, is_active=True, manager_user_id=uuid4())
        ),
    )
    handler = GetClientByIdHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(AccessDeniedError):
        await handler.handle(
            GetClientByIdQuery(
                client_id=client_id, actor_user_id=uuid4(), actor_role=Role.CLUB_MANAGER
            )
        )


@pytest.mark.unit
async def test_get_client_by_id_raises_when_missing() -> None:
    uow = FakeUnitOfWork()
    handler = GetClientByIdHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(ClientNotFoundError):
        await handler.handle(
            GetClientByIdQuery(
                client_id=uuid4(), actor_user_id=uuid4(), actor_role=Role.NETWORK_ADMIN
            )
        )


@pytest.mark.unit
async def test_get_client_by_user_id_raises_when_missing() -> None:
    uow = FakeUnitOfWork()
    handler = GetClientByUserIdHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(ClientNotFoundError):
        await handler.handle(
            GetClientByUserIdQuery(
                user_id=uuid4(), actor_user_id=uuid4(), actor_role=Role.CLIENT
            )
        )


# ---------------------------------------------------------------------------
# ListClientsByClubHandler
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_list_clients_allows_network_admin() -> None:
    club_id = uuid4()
    page = ClientPageReadModel(items=[], total=0)
    uow = FakeUnitOfWork(clients_read=FakeClientReadRepository(page=page))
    handler = ListClientsByClubHandler(FakeUnitOfWorkFactory(uow))

    result = await handler.handle(
        ListClientsByClubQuery(
            club_id=club_id, actor_user_id=uuid4(), actor_role=Role.NETWORK_ADMIN
        )
    )

    assert result is page


@pytest.mark.unit
async def test_list_clients_allows_matching_manager() -> None:
    club_id = uuid4()
    manager_id = uuid4()
    page = ClientPageReadModel(items=[], total=0)
    uow = FakeUnitOfWork(
        clients_read=FakeClientReadRepository(page=page),
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(
                club_id=club_id, is_active=True, manager_user_id=manager_id
            )
        ),
    )
    handler = ListClientsByClubHandler(FakeUnitOfWorkFactory(uow))

    result = await handler.handle(
        ListClientsByClubQuery(
            club_id=club_id, actor_user_id=manager_id, actor_role=Role.CLUB_MANAGER
        )
    )

    assert result is page


@pytest.mark.unit
async def test_list_clients_denies_client_role() -> None:
    uow = FakeUnitOfWork()
    handler = ListClientsByClubHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(AccessDeniedError):
        await handler.handle(
            ListClientsByClubQuery(
                club_id=uuid4(), actor_user_id=uuid4(), actor_role=Role.CLIENT
            )
        )


@pytest.mark.unit
async def test_list_clients_denies_manager_of_other_club() -> None:
    club_id = uuid4()
    uow = FakeUnitOfWork(
        club_snapshots=FakeClubSnapshotRepository(
            ClubScopeSnapshot(club_id=club_id, is_active=True, manager_user_id=uuid4())
        )
    )
    handler = ListClientsByClubHandler(FakeUnitOfWorkFactory(uow))

    with pytest.raises(AccessDeniedError):
        await handler.handle(
            ListClientsByClubQuery(
                club_id=club_id, actor_user_id=uuid4(), actor_role=Role.CLUB_MANAGER
            )
        )
