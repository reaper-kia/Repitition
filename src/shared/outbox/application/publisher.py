import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
import logging
import random
from typing import Any, Protocol
from uuid import uuid4

from src.shared.application.unit_of_work import UnitOfWorkFactory

logger = logging.getLogger(__name__)


class KafkaJsonProducer(Protocol):
    async def send_json(
        self,
        *,
        topic: str,
        key: str,
        value: Mapping[str, Any],
    ) -> object: ...


def calculate_retry_delay_seconds(attempts: int) -> int:
    base_delays = [5, 15, 30, 60, 300, 900]
    index = min(attempts, len(base_delays) - 1)
    base_delay = base_delays[index]
    jitter = random.randint(0, max(1, int(base_delay * 0.2)))
    return base_delay + jitter


@dataclass
class OutboxPublisher:
    uow_factory: UnitOfWorkFactory
    producer: KafkaJsonProducer
    batch_size: int = 100
    worker_id: str = ""

    async def publish_once(self) -> int:
        if not self.worker_id:
            self.worker_id = f"outbox-publisher-{uuid4()}"

        published_count = 0

        async with self.uow_factory() as uow:
            messages = await uow.outbox.get_pending_batch_for_update(
                limit=self.batch_size,
                worker_id=self.worker_id,
            )

            for message in messages:
                try:
                    await self.producer.send_json(
                        topic=message.topic,
                        key=message.key,
                        value=message.payload,
                    )
                # Producer — внешний адаптер; любую его ошибку сохраняем в outbox.
                except Exception as exc:
                    retry_delay = calculate_retry_delay_seconds(message.attempts)
                    message.mark_failed(
                        error=str(exc),
                        retry_after_seconds=retry_delay,
                    )
                    await uow.outbox.save(message)

                    logger.exception(
                        "Failed to publish outbox message event_id=%s",
                        message.event_id,
                    )
                    continue

                message.mark_published()
                await uow.outbox.save(message)
                published_count += 1

            await uow.commit()

        return published_count

    async def run_forever(self, *, interval_seconds: float = 1.0) -> None:
        while True:
            try:
                published_count = await self.publish_once()

                if published_count > 0:
                    logger.info(
                        "Published %s outbox message(s)",
                        published_count,
                    )
            except asyncio.CancelledError:
                raise
            # Вечный воркер не должен завершаться из-за одной неудачной итерации.
            except Exception:
                logger.exception("Outbox publisher iteration failed")

            await asyncio.sleep(interval_seconds)
