from dataclasses import dataclass, field
from typing import Any

from aiokafka import AIOKafkaConsumer

from src.shared.infra.kafka.json import decode_json, decode_key


@dataclass(frozen=True)
class KafkaConsumedMessage:
    topic: str
    partition: int
    offset: int
    key: str | None
    value: dict[str, Any]


@dataclass
class KafkaEventConsumer:
    bootstrap_servers: str
    client_id: str
    group_id: str
    topic: str
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = False
    _consumer: AIOKafkaConsumer | None = field(
        default=None,
        init=False,
        repr=False,
    )

    async def start(self) -> None:
        if self._consumer is not None:
            return

        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            client_id=self.client_id,
            group_id=self.group_id,
            key_deserializer=decode_key,
            value_deserializer=decode_json,
            auto_offset_reset=self.auto_offset_reset,
            enable_auto_commit=self.enable_auto_commit,
        )

        await self._consumer.start()

    async def stop(self) -> None:
        if self._consumer is None:
            return

        await self._consumer.stop()

        self._consumer = None

    async def get_one(self) -> KafkaConsumedMessage:
        if self._consumer is None:
            raise RuntimeError("Kafka consumer is stopped")

        record = await self._consumer.getone()

        return KafkaConsumedMessage(
            topic=record.topic,
            partition=record.partition,
            offset=record.offset,
            key=record.key,
            value=record.value,
        )

    async def commit(self) -> None:
        if self._consumer is None:
            raise RuntimeError("Kafka consumer is stopped")

        await self._consumer.commit()
