from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from src.shared.infra.redis.json_cache import RedisJsonCache
from src.shared.infra.redis.rate_limiter import RedisFixedWindowRateLimiter


@pytest.mark.unit
@pytest.mark.asyncio
async def test_json_cache_sets_serialized_value() -> None:
    redis = SimpleRedis()
    cache = RedisJsonCache(redis=redis, key_prefix="app")

    result = await cache.set_json(
        "items",
        {"items": [1, 2]},
        ttl_seconds=30,
    )

    assert result is True
    redis.set.assert_awaited_once_with(
        "app:cache:items",
        '{"items": [1, 2]}',
        ex=30,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_json_cache_reads_object() -> None:
    redis = SimpleRedis()
    redis.get.return_value = b'{"value": 1}'
    cache = RedisJsonCache(redis=redis, key_prefix="app")

    assert await cache.get_json("key") == {"value": 1}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_allows_request_at_limit_boundary() -> None:
    redis = SimpleRedis()
    redis.set.return_value = False
    redis.incr.return_value = 5
    limiter = RedisFixedWindowRateLimiter(redis=redis, key_prefix="auth")

    result = await limiter.hit(key="login:ip", limit=5, window_seconds=60)

    assert result.allowed is True
    assert result.attempts == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_blocks_request_above_limit() -> None:
    redis = SimpleRedis()
    redis.set.return_value = False
    redis.incr.return_value = 6
    redis.ttl.return_value = 42
    limiter = RedisFixedWindowRateLimiter(redis=redis, key_prefix="auth")

    result = await limiter.hit(key="login:ip", limit=5, window_seconds=60)

    assert result.allowed is False
    assert result.retry_after_seconds == 42


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_fails_open_when_redis_is_down() -> None:
    redis = SimpleRedis()
    redis.set.side_effect = RedisConnectionError("down")
    limiter = RedisFixedWindowRateLimiter(redis=redis, key_prefix="auth")

    result = await limiter.hit(key="login:ip", limit=5, window_seconds=60)

    assert result.allowed is True
    assert result.degraded is True


class SimpleRedis:
    def __init__(self) -> None:
        self.set = AsyncMock(return_value=True)
        self.get = AsyncMock(return_value=None)
        self.incr = AsyncMock(return_value=1)
        self.ttl = AsyncMock(return_value=60)
        self.delete = AsyncMock(return_value=0)

    async def scan_iter(self, **kwargs):
        if False:
            yield None
