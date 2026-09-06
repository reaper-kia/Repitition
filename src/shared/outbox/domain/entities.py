from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from src.shared.events.integration_event import IntegrationEvent
from src.shared.outbox.domain.enums import OutboxMessageStatus


@dataclass
class OutboxMessage:
    topic: str
    key: str
    event_id: UUID
    event_type: str
    event_version: int
    aggregate_type: str
    aggregate_id: UUID
    payload: Mapping[str, Any]
    metadata: Mapping[str, Any]
    id: UUID = field(default_factory=uuid4)
    status: OutboxMessageStatus = OutboxMessageStatus.PENDING
    attempts: int = 0
    max_attempts: int = 10
    available_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    locked_at: datetime | None = None
    locked_by: str | None = None
    published_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_event(
        cls,
        *,
        event: IntegrationEvent,
        topic: str,
        key: str,
        max_attempts: int = 10,
    ) -> "OutboxMessage":
        return cls(
            topic=topic,
            key=key,
            event_id=event.event_id,
            event_type=event.event_type,
            event_version=event.event_version,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            payload=event.to_payload(),
            metadata=dict(event.metadata),
            max_attempts=max_attempts,
        )

    def mark_processing(self, *, worker_id: str) -> None:
        self.status = OutboxMessageStatus.PROCESSING
        self.locked_by = worker_id
        self.locked_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def mark_published(self) -> None:
        self.status = OutboxMessageStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
        self.locked_by = None
        self.locked_at = None
        self.last_error = None
        self.updated_at = datetime.now(UTC)

    def mark_failed(self, *, error: str, retry_after_seconds: int) -> None:
        self.attempts += 1
        self.last_error = error
        self.locked_by = None
        self.locked_at = None
        self.updated_at = datetime.now(UTC)

        if self.attempts >= self.max_attempts:
            self.status = OutboxMessageStatus.FAILED
            return

        self.status = OutboxMessageStatus.PENDING
        self.available_at = datetime.now(UTC) + timedelta(seconds=retry_after_seconds)
