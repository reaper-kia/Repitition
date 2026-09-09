"""Шаблон Kafka-консьюмера.

Заменяет удалённый доменный консьюмер и сохраняет всю обвязку:
ретраи, DLQ, ручной commit офсета. Логика обработки события вынесена
в одну функцию handle_event - её и надо заменить под свой кейс.

Запуск:
    docker compose --profile events up
    python -m src.workers.event_consumer

Профиль events поднимает Kafka и воркеры. Без него стек стартует
без Kafka - быстрее на старте, а на хакатоне это важно.
"""

import asyncio
import logging
from typing import Any

from src.core.config import settings
from src.shared.infra.kafka.consumer import KafkaConsumedMessage, KafkaEventConsumer
from src.shared.infra.kafka.dlq import create_dlq_key, create_dlq_payload
from src.shared.infra.kafka.producer import KafkaEventProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_event(payload: dict[str, Any]) -> None:
    """ЗАМЕНИ ЭТО под свой кейс.

    payload - это тело события в формате IntegrationEvent.to_payload():
    event_id, event_type, event_version, occurred_at, producer,
    aggregate_type, aggregate_id, payload, metadata.

    Если нужен доступ к базе - возьми фабрику UoW:
        from src.shared.api.dependencies import get_unit_of_work_factory
        uow_factory = get_unit_of_work_factory()
        async with uow_factory() as uow:
            ...
            await uow.commit()
    """
    logger.info(
        "Получено событие %s (aggregate=%s)",
        payload.get("event_type"),
        payload.get("aggregate_id"),
    )


async def process_with_retries(
    message: KafkaConsumedMessage,
    producer: KafkaEventProducer,
) -> None:
    """Обрабатывает сообщение с повторами, при исчерпании - отправляет в DLQ."""
    last_error: BaseException | None = None

    for attempt in range(1, settings.kafka_consumer_max_attempts + 1):
        try:
            await handle_event(message.value)
            return
        # Обработчик доменного события заменяется пользователем и может бросить
        # исключение любого типа: здесь оно намеренно становится причиной retry.
        except Exception as error:  # noqa: BLE001
            last_error = error
            logger.warning(
                "Попытка %s/%s не удалась: %s",
                attempt,
                settings.kafka_consumer_max_attempts,
                error,
            )
            if attempt < settings.kafka_consumer_max_attempts:
                await asyncio.sleep(settings.kafka_consumer_retry_delay_seconds)

    logger.error("Отправляю сообщение в DLQ после всех попыток")
    await producer.send_json(
        topic=settings.kafka_events_dlq_topic,
        key=create_dlq_key(message),
        value=create_dlq_payload(
            message=message,
            error=last_error or RuntimeError("unknown error"),
            attempts=settings.kafka_consumer_max_attempts,
        ),
    )


async def main() -> None:
    consumer = KafkaEventConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=settings.kafka_client_id,
        group_id=settings.kafka_events_consumer_group,
        topic=settings.kafka_events_topic,
    )
    producer = KafkaEventProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=f"{settings.kafka_client_id}-dlq",
    )

    await consumer.start()
    await producer.start()
    logger.info("Event consumer started on topic %s", settings.kafka_events_topic)

    try:
        while True:
            message = await consumer.get_one()
            await process_with_retries(message, producer)
            # Коммитим офсет только после успешной обработки или ухода в DLQ,
            # иначе при падении воркера сообщение потеряется.
            await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()
        logger.info("Event consumer stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Event consumer interrupted")
