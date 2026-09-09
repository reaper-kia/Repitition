from redis.asyncio import Redis
from redis.exceptions import RedisError


async def check_redis_connection(redis: Redis) -> bool:
    try:
        return bool(await redis.ping())
    except RedisError:
        return False
