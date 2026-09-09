from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.outbox.domain.entities import OutboxMessage
from src.shared.outbox.domain.enums import OutboxMessageStatus
from src.shared.outbox.infra.models import OutboxMessageModel


class SQLAlchemyOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, message: OutboxMessage) -> OutboxMessage:
        model = self._to_model(message)
        self.session.add(model)
        return message

    async def get_pending_batch_for_update(
        self,
        *,
        limit: int,
        worker_id: str,
    ) -> list[OutboxMessage]:
        stmt = (
            select(OutboxMessageModel)
            .where(
                OutboxMessageModel.status == OutboxMessageStatus.PENDING.value,
                OutboxMessageModel.available_at <= datetime.now(UTC),
            )
            .order_by(OutboxMessageModel.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        result = await self.session.execute(stmt)
        models = list(result.scalars().all())

        messages: list[OutboxMessage] = []

        for model in models:
            message = self._to_entity(model)
            message.mark_processing(worker_id=worker_id)

            self._apply_entity_to_model(message, model)
            messages.append(message)

        return messages

    async def save(self, message: OutboxMessage) -> None:
        model = await self.session.get(OutboxMessageModel, message.id)

        if model is None:
            raise ValueError(f"Outbox message {message.id} not found")

        self._apply_entity_to_model(message, model)

    async def mark_as_published(self, message_id: UUID) -> None:
        model = await self.session.get(OutboxMessageModel, message_id)

        if model is None:
            raise ValueError(f"Outbox message {message_id} not found")

        message = self._to_entity(model)
        message.mark_published()
        self._apply_entity_to_model(message, model)

    def _to_model(self, message: OutboxMessage) -> OutboxMessageModel:
        return OutboxMessageModel(
            id=message.id,
            topic=message.topic,
            key=message.key,
            event_id=message.event_id,
            event_type=message.event_type,
            event_version=message.event_version,
            aggregate_type=message.aggregate_type,
            aggregate_id=message.aggregate_id,
            payload=dict(message.payload),
            metadata_json=dict(message.metadata),
            status=message.status.value,
            attempts=message.attempts,
            max_attempts=message.max_attempts,
            available_at=message.available_at,
            locked_at=message.locked_at,
            locked_by=message.locked_by,
            published_at=message.published_at,
            last_error=message.last_error,
            created_at=message.created_at,
            updated_at=message.updated_at,
        )

    def _to_entity(self, model: OutboxMessageModel) -> OutboxMessage:
        return OutboxMessage(
            id=model.id,
            topic=model.topic,
            key=model.key,
            event_id=model.event_id,
            event_type=model.event_type,
            event_version=model.event_version,
            aggregate_type=model.aggregate_type,
            aggregate_id=model.aggregate_id,
            payload=model.payload,
            metadata=model.metadata_json,
            status=OutboxMessageStatus(model.status),
            attempts=model.attempts,
            max_attempts=model.max_attempts,
            available_at=model.available_at,
            locked_at=model.locked_at,
            locked_by=model.locked_by,
            published_at=model.published_at,
            last_error=model.last_error,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _apply_entity_to_model(
        self,
        message: OutboxMessage,
        model: OutboxMessageModel,
    ) -> None:
        model.topic = message.topic
        model.key = message.key
        model.event_id = message.event_id
        model.event_type = message.event_type
        model.event_version = message.event_version
        model.aggregate_type = message.aggregate_type
        model.aggregate_id = message.aggregate_id
        model.payload = dict(message.payload)
        model.metadata_json = dict(message.metadata)
        model.status = message.status.value
        model.attempts = message.attempts
        model.max_attempts = message.max_attempts
        model.available_at = message.available_at
        model.locked_at = message.locked_at
        model.locked_by = message.locked_by
        model.published_at = message.published_at
        model.last_error = message.last_error
        model.created_at = message.created_at
        model.updated_at = message.updated_at
