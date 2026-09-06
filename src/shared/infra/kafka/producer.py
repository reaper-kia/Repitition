import json
from collections.abc import Mapping
from typing import Any

from aiokafka import AIOKafkaProducer


class KafkaEventProducer:
    def __init__(
        self,
        *,
        bootstrap_servers: str,
        client_id: str,
    ) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
            acks="all",
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda key: key.encode("utf-8"),
        )

    async def start(self) -> None:
        await self._producer.start()

    async def stop(self) -> None:
        await self._producer.stop()

    async def send_json(
        self,
        *,
        topic: str,
        key: str,
        value: Mapping[str, Any],
    ) -> object:
        return await self._producer.send_and_wait(
            topic=topic,
            key=key,
            value=dict(value),
        )
