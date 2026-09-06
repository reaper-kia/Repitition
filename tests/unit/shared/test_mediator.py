from dataclasses import dataclass

import pytest

from src.shared.application.mediator import Mediator


@dataclass(frozen=True)
class Query:
    value: int


class Handler:
    async def handle(self, query: Query) -> int:
        return query.value * 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mediator_dispatches_registered_message() -> None:
    mediator = Mediator()
    mediator.register(Query, Handler())

    assert await mediator.send(Query(4)) == 8


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mediator_rejects_unregistered_message() -> None:
    mediator = Mediator()

    with pytest.raises(RuntimeError, match="No handler for message type Query"):
        await mediator.send(Query(1))
