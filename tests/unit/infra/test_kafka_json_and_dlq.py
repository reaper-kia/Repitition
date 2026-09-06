from uuid import UUID

import pytest

from src.shared.infra.kafka.consumer import KafkaConsumedMessage
from src.shared.infra.kafka.dlq import create_dlq_key, create_dlq_payload
from src.shared.infra.kafka.json import decode_json, decode_key, encode_json, encode_key


@pytest.mark.unit
def test_kafka_key_roundtrip() -> None:
    assert decode_key(encode_key("abc")) == "abc"
    assert encode_key(None) is None
    assert decode_key(None) is None


@pytest.mark.unit
def test_kafka_json_roundtrip_supports_uuid() -> None:
    value = {"id": UUID("80000000-0000-0000-0000-000000000001")}

    decoded = decode_json(encode_json(value))

    assert decoded == {"id": "80000000-0000-0000-0000-000000000001"}


@pytest.mark.unit
def test_kafka_json_rejects_non_object() -> None:
    with pytest.raises(TypeError, match="must be an object"):
        decode_json(b"[]")


@pytest.mark.unit
def test_dlq_payload_preserves_original_message() -> None:
    message = KafkaConsumedMessage(
        topic="events",
        partition=2,
        offset=42,
        key=None,
        value={"hello": "world"},
    )

    payload = create_dlq_payload(
        message=message,
        error=RuntimeError("boom"),
        attempts=3,
    )

    assert create_dlq_key(message) == "events:2:42"
    assert payload["original_topic"] == "events"
    assert payload["original_offset"] == 42
    assert payload["attempts"] == 3
    assert payload["error_type"] == "RuntimeError"
    assert payload["payload"] == {"hello": "world"}
