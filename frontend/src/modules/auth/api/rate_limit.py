from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from src.shared.infra.redis.dependencies import get_redis_client
from src.shared.infra.redis.rate_limiter import RedisFixedWindowRateLimiter
from src.core.config import settings


def get_client_ip(request: Request) -> str:
    if request.client is None:
        return "unknown"

    return request.client.host


def get_rate_limiter(
    redis: Redis = Depends(get_redis_client),
) -> RedisFixedWindowRateLimiter:
    return RedisFixedWindowRateLimiter(
        redis=redis,
        key_prefix=settings.redis_key_prefix,
    )


async def check_auth_rate_limit(
    *,
    request: Request,
    limiter: RedisFixedWindowRateLimiter,
    action: str,
    limit: int,
    window_seconds: int,
) -> None:
    client_ip = get_client_ip(request)

    result = await limiter.hit(
        key=f"rate_limit:auth:{action}:ip:{client_ip}",
        limit=limit,
        window_seconds=window_seconds,
    )

    if result.allowed:
        return

    retry_after_seconds = result.retry_after_seconds or window_seconds

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many request. Try again later.",
        headers={"Retry-After": str(retry_after_seconds)},
    )


async def limit_login_request(
    request: Request,
    limiter: RedisFixedWindowRateLimiter = Depends(get_rate_limiter),
) -> None:
    await check_auth_rate_limit(
        request=request,
        limiter=limiter,
        action="login",
        limit=settings.auth_login_rate_limit,
        window_seconds=settings.auth_login_rate_limit_window_seconds,
    )


async def limit_register_request(
    request: Request,
    limiter: RedisFixedWindowRateLimiter = Depends(get_rate_limiter),
) -> None:
    await check_auth_rate_limit(
        request=request,
        limiter=limiter,
        action="register",
        limit=settings.auth_register_rate_limit,
        window_seconds=settings.auth_register_rate_limit_window_seconds,
    )
