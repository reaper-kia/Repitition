from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user_id
from src.modules.users.api.dependencies import get_mediator
from src.modules.users.api.router import router as users_router
from src.modules.users.application.queries.get_user_by_id import GetUserByIdQuery
from src.modules.users.application.read_models import UserReadModel
from src.modules.users.domain.enums import Role


USER_ID = UUID("21000000-0000-0000-0000-000000000001")


@dataclass
class StubMediator:
    result: UserReadModel
    received: Any = None

    async def send(self, message: Any) -> UserReadModel:
        self.received = message
        return self.result


@pytest.mark.api
def test_users_me_returns_role_and_not_legacy_admin_flag() -> None:
    mediator = StubMediator(
        UserReadModel(
            id=USER_ID,
            name="Network Admin",
            email="admin@example.com",
            role=Role.NETWORK_ADMIN,
        )
    )
    app = FastAPI()
    app.include_router(users_router)
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    app.dependency_overrides[get_mediator] = lambda: mediator

    with TestClient(app) as client:
        response = client.get("/users/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(USER_ID),
        "name": "Network Admin",
        "email": "admin@example.com",
        "role": "NETWORK_ADMIN",
    }
    assert "is_admin" not in response.json()
    assert mediator.received == GetUserByIdQuery(id=USER_ID)
