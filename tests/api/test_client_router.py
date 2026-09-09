from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.auth.api.actor import RequestActor
from src.modules.auth.api.dependencies import get_current_actor
from src.modules.client.api.dependencies import (
    get_client_by_id_handler,
    get_client_by_user_id_handler,
    get_register_client_handler,
    list_clients_by_club_handler,
)
from src.modules.client.api.router import router as client_router
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
)
from src.modules.client.domain.value_objects import Membership, ReferralCode
from src.modules.users.domain.enums import Role


class StubHandler:
    """Подмена реального хендлера — тест проверяет только HTTP-контракт,
    не бизнес-логику (та уже покрыта в tests/unit/client/test_client.py)."""

    def __init__(self, *, result=None, exc: Exception | None = None) -> None:
        self.result = result
        self.exc = exc
        self.received = None

    async def handle(self, arg):
        self.received = arg
        if self.exc is not None:
            raise self.exc
        return self.result


def _make_app() -> tuple[FastAPI, dict[str, StubHandler]]:
    app = FastAPI()
    app.include_router(client_router)

    handlers = {
        "register": StubHandler(),
        "by_id": StubHandler(),
        "by_user_id": StubHandler(),
        "list": StubHandler(),
    }
    app.dependency_overrides[get_register_client_handler] = lambda: handlers["register"]
    app.dependency_overrides[get_client_by_id_handler] = lambda: handlers["by_id"]
    app.dependency_overrides[get_client_by_user_id_handler] = lambda: handlers[
        "by_user_id"
    ]
    app.dependency_overrides[list_clients_by_club_handler] = lambda: handlers["list"]

    return app, handlers


def _override_actor(app: FastAPI, actor: RequestActor) -> None:
    app.dependency_overrides[get_current_actor] = lambda: actor


def _client() -> Client:
    return Client.register(
        user_id=uuid4(),
        club_id=uuid4(),
        display_name="New Client",
        membership=Membership(
            type=MembershipType.ONE_MONTH, expires_at=datetime(2030, 1, 1, tzinfo=UTC)
        ),
        referral_code=ReferralCode("ABCDEF"),
    )


def _read_model(client: Client) -> ClientReadModel:
    return ClientReadModel(
        id=client.id,
        user_id=client.user_id,
        club_id=client.club_id,
        display_name=client.display_name,
        membership_type=client.membership.type,
        membership_expires_at=client.membership.expires_at,
        referral_code=client.referral_code.value,
        referred_by_client_id=client.referred_by_client_id,
        acquisition_channel=client.acquisition_channel,
        status=client.status,
        registered_at=client.registered_at,
    )


@pytest.mark.api
def test_register_client_uses_actor_identity_not_stub_name() -> None:
    app, handlers = _make_app()
    actor = RequestActor(user_id=uuid4(), role=Role.CLIENT, name="Реальное Имя")
    _override_actor(app, actor)
    handlers["register"].result = _client()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/clients",
            json={"club_id": str(uuid4()), "membership_type": "ONE_MONTH"},
        )

    assert response.status_code == 201
    cmd = handlers["register"].received
    # Регрессия на старую заглушку "Test User": имя и user_id должны быть
    # взяты из актора, а не из фейковой зависимости.
    assert cmd.user_id == actor.user_id
    assert cmd.display_name == "Реальное Имя"


@pytest.mark.api
def test_register_client_maps_already_exists_to_409() -> None:
    app, handlers = _make_app()
    _override_actor(app, RequestActor(user_id=uuid4(), role=Role.CLIENT, name="X"))
    handlers["register"].exc = ClientAlreadyExistsError("dup")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/clients",
            json={"club_id": str(uuid4()), "membership_type": "ONE_MONTH"},
        )

    assert response.status_code == 409


@pytest.mark.api
def test_register_client_maps_inactive_club_to_422() -> None:
    app, handlers = _make_app()
    _override_actor(app, RequestActor(user_id=uuid4(), role=Role.CLIENT, name="X"))
    handlers["register"].exc = ClubInactiveError("inactive")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/clients",
            json={"club_id": str(uuid4()), "membership_type": "ONE_MONTH"},
        )

    assert response.status_code == 422


@pytest.mark.api
def test_get_my_client_passes_actor_role_and_id() -> None:
    app, handlers = _make_app()
    actor = RequestActor(user_id=uuid4(), role=Role.CLIENT, name="X")
    _override_actor(app, actor)
    model = _read_model(_client())
    handlers["by_user_id"].result = model

    with TestClient(app) as client:
        response = client.get("/api/v1/clients/me")

    assert response.status_code == 200
    query = handlers["by_user_id"].received
    assert query.user_id == actor.user_id
    assert query.actor_role is Role.CLIENT
    assert response.json()["id"] == str(model.id)


@pytest.mark.api
def test_get_my_client_maps_not_found_to_404() -> None:
    app, handlers = _make_app()
    _override_actor(app, RequestActor(user_id=uuid4(), role=Role.CLIENT, name="X"))
    handlers["by_user_id"].exc = ClientNotFoundError("nope")

    with TestClient(app) as client:
        response = client.get("/api/v1/clients/me")

    assert response.status_code == 404


@pytest.mark.api
def test_get_client_by_id_maps_access_denied_to_403() -> None:
    app, handlers = _make_app()
    _override_actor(app, RequestActor(user_id=uuid4(), role=Role.CLIENT, name="X"))
    handlers["by_id"].exc = AccessDeniedError("nope")

    with TestClient(app) as client:
        response = client.get(f"/api/v1/clients/{uuid4()}")

    assert response.status_code == 403


@pytest.mark.api
def test_list_club_clients_passes_pagination_and_actor() -> None:
    app, handlers = _make_app()
    actor = RequestActor(user_id=uuid4(), role=Role.NETWORK_ADMIN, name="X")
    _override_actor(app, actor)
    club_id = uuid4()
    handlers["list"].result = ClientPageReadModel(items=[], total=0)

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/clubs/{club_id}/clients", params={"page": 2, "page_size": 10}
        )

    assert response.status_code == 200
    query = handlers["list"].received
    assert query.club_id == club_id
    assert query.page == 2
    assert query.page_size == 10
    assert query.actor_role is Role.NETWORK_ADMIN


@pytest.mark.api
def test_list_club_clients_maps_access_denied_to_403() -> None:
    app, handlers = _make_app()
    _override_actor(app, RequestActor(user_id=uuid4(), role=Role.CLIENT, name="X"))
    handlers["list"].exc = AccessDeniedError("nope")

    with TestClient(app) as client:
        response = client.get(f"/api/v1/clubs/{uuid4()}/clients")

    assert response.status_code == 403
