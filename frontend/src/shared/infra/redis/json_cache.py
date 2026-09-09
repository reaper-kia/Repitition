import json
from dataclasses import dataclass

from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.shared.application.cache import JSONValue, JsonCache


@dataclass(slots=True)
class RedisJsonCache(JsonCache):
    redis: Redis
    key_prefix: str

    def _redis_key(self, key: str) -> str:
        return f"{self.key_prefix}:cache:{key}"

    async def get_json(self, key: str) -> JSONValue | None:
        redis_key = self._redis_key(key)

        try:
            raw_value = await self.redis.get(redis_key)
        except RedisError:
            return None

        if raw_value is None:
            return None

        try:
            value = json.loads(raw_value)
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
            return None

        if not isinstance(value, (dict, list)):
            return None

        return value

    async def set_json(self, key: str, value: JSONValue, *, ttl_seconds: int):
        redis_key = self._redis_key(key)

        try:
            raw_value = json.dumps(value)
            await self.redis.set(
                redis_key,
                raw_value,
                ex=ttl_seconds,
            )
            return True
        except (RedisError, TypeError, ValueError):
            return False

    async def delete(self, *keys) -> int:
        if not keys:
            return 0

        redis_keys = [self._redis_key(key) for key in keys]

        try:
            return int(await self.redis.delete(*redis_keys))
        except (RedisError, TypeError, ValueError):
            return 0

    async def delete_by_pattern(self, pattern: str) -> int:
        redis_pattern = self._redis_key(pattern)
        deleted = 0
        batch: list[str] = []

        try:
            async for redis_key in self.redis.scan_iter(
                match=redis_pattern,
                count=100,
            ):
                batch.append(redis_key)

                if len(batch) >= 100:
                    deleted += int(await self.redis.delete(*batch))
                    batch.clear()
            if batch:
                deleted += int(await self.redis.delete(*batch))

            return deleted
        except (RedisError, TypeError, ValueError):
            return 0
