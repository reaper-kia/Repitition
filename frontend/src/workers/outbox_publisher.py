import asyncio
import logging

from src.core.config import settings
from src.shared.api.dependencies import get_unit_of_work_factory
from src.shared.infra.kafka.producer import KafkaEventProducer
from src.shared.outbox.application.publisher import OutboxPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    producer = KafkaEventProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=settings.kafka_client_id,
    )

    await producer.start()
    logger.info("Outbox publisher started")

    try:
        publisher = OutboxPublisher(
            uow_factory=get_unit_of_work_factory(),
            producer=producer,
            batch_size=settings.outbox_publisher_batch_size,
        )

        await publisher.run_forever(
            interval_seconds=settings.outbox_publisher_poll_interval_seconds,
        )
    finally:
        await producer.stop()
        logger.info("Outbox publisher stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Outbox publisher interrupted")
