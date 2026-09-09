from typing import Protocol
from uuid import UUID

from src.shared.outbox.domain.entities import OutboxMessage


class OutboxRepository(Protocol):
    async def add(self, message: OutboxMessage) -> OutboxMessage: ...

    async def get_pending_batch_for_update(
        self,
        *,
        limit: int,
        worker_id: str,
    ) -> list[OutboxMessage]: ...

    async def save(self, message: OutboxMessage) -> None: ...

    async def mark_as_published(self, message_id: UUID) -> None: ...
