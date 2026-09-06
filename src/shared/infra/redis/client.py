from redis.asyncio import Redis

from src.core.config import settings

redis_client = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def close_redis_client() -> None:
    await redis_client.aclose()
