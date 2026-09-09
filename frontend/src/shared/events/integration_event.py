from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import UUID, uuid4


@dataclass(frozen=True)
class IntegrationEvent:
    event_type: str
    data: Mapping[str, Any]
    aggregate_type: str
    aggregate_id: UUID
    event_version: int = 1
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    producer: str = "hackathon-api"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "producer": self.producer,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": str(self.aggregate_id),
            "payload": dict(self.data),
            "metadata": dict(self.metadata),
        }
