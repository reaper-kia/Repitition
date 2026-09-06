from datetime import UTC, datetime
from typing import Any

from src.shared.infra.kafka.consumer import KafkaConsumedMessage


def create_dlq_key(message: KafkaConsumedMessage):
    if message.key is not None:
        return message.key

    return f"{message.topic}:{message.partition}:{message.offset}"


def create_dlq_payload(
    *,
    message: KafkaConsumedMessage,
    error: BaseException,
    attempts: int,
) -> dict[str, Any]:
    return {
        "original_topic": message.topic,
        "original_partition": message.partition,
        "original_offset": message.offset,
        "original_key": message.key,
        "failed_at": datetime.now(UTC).isoformat(),
        "attempts": attempts,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "payload": message.value,
    }
