from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.modules.auth.api.actor import RequestActor
from src.modules.auth.api.dependencies import get_current_actor, require_roles
from src.modules.users.application.queries.get_user_by_id import GetUserByIdQuery
from src.modules.users.application.read_models import UserReadModel
from src.modules.users.domain.enums import Role


USER_ID = UUID("22000000-0000-0000-0000-000000000001")
NETWORK_ADMIN_REQUIRED = require_roles(Role.NETWORK_ADMIN)


@dataclass
class StubMediator:
    result: UserReadModel
    received: Any = None

    async def send(self, message: Any) -> UserReadModel:
        self.received = message
        return self.result


def build_guarded_app(actor: RequestActor) -> FastAPI:
    app = FastAPI()

    @app.get("/admin-only")
    async def admin_only(
        current_actor: RequestActor = Depends(NETWORK_ADMIN_REQUIRED),
    ) -> dict[str, str]:
        return {"user_id": str(current_actor.user_id)}

    app.dependency_overrides[get_current_actor] = lambda: actor
    return app


@pytest.mark.api
def test_require_roles_allows_network_admin() -> None:
    app = build_guarded_app(
        RequestActor(
            user_id=USER_ID,
            role=Role.NETWORK_ADMIN,
            name="Admin",
        )
    )

    with TestClient(app) as client:
        response = client.get("/admin-only")

    assert response.status_code == 200
    assert response.json() == {"user_id": str(USER_ID)}


@pytest.mark.api
def test_require_roles_rejects_client() -> None:
    app = build_guarded_app(
        RequestActor(
            user_id=USER_ID,
            role=Role.CLIENT,
            name="Client",
        )
    )

    with TestClient(app) as client:
        response = client.get("/admin-only")

    assert response.status_code == 403
    assert response.json() == {"detail": "ACCESS_DENIED"}


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_current_actor_uses_registered_user_query() -> None:
    mediator = StubMediator(
        UserReadModel(
            id=USER_ID,
            name="Admin",
            email="admin@example.com",
            role=Role.NETWORK_ADMIN,
        )
    )

    actor = await get_current_actor(user_id=USER_ID, mediator=mediator)

    assert actor == RequestActor(
        user_id=USER_ID,
        role=Role.NETWORK_ADMIN,
        name="Admin",
    )
    assert mediator.received == GetUserByIdQuery(id=USER_ID)
