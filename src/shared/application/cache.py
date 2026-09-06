from typing import Any, Protocol


JSONValue = dict[str, Any] | list[Any]


class JsonCache(Protocol):
    async def get_json(self, key: str) -> JSONValue | None: ...

    async def set_json(
        self, key: str, value: JSONValue, *, ttl_seconds: int
    ) -> bool: ...

    async def delete(self, *keys: str) -> int: ...

    async def delete_by_pattern(self, pattern: str) -> int: ...


class NullJsonCache:
    async def get_json(self, key: str) -> JSONValue | None:
        return None

    async def set_json(self, key: str, value: JSONValue, *, ttl_seconds: int) -> bool:
        return False

    async def delete(self, *keys: str) -> int:
        return 0

    async def delete_by_pattern(self, pattern: str) -> int:
        return 0
