import json as json_lib
from collections.abc import Mapping
from typing import Any


def encode_key(key: str | None) -> bytes | None:
    if key is None:
        return None

    return key.encode("utf-8")


def decode_key(raw_key: bytes | None) -> str | None:
    if raw_key is None:
        return None

    return raw_key.decode("utf-8")


def encode_json(value: Mapping[str, Any]) -> bytes:
    return json_lib.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def decode_json(raw_value: bytes) -> dict[str, Any]:
    value = json_lib.loads(raw_value.decode("utf-8"))

    if not isinstance(value, dict):
        raise TypeError("Kafka JSON message value must be an object")

    return value
