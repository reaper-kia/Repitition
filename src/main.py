from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.modules.auth.api.router import router as auth_router
from src.modules.users.api.router import router as users_router
from src.modules.club.api.router import router as club_router
# Временно отключаем остальные нереализованные модули
# from src.modules.achivement.api.router import router as achivement_router
# from src.modules.client.api.router import router as client_router
# from src.modules.rewards.api.router import router as rewards_router
# from src.modules.visit.api.router import router as visit_router
from src.shared.infra.database.health import check_database_connection
from src.shared.infra.database.session import get_async_session
from src.shared.infra.redis.client import close_redis_client
from src.shared.infra.redis.dependencies import get_redis_client
from src.shared.infra.redis.health import check_redis_connection


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await close_redis_client()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(users_router)
    app.include_router(auth_router)
    app.include_router(club_router)
    # app.include_router(achivement_router)
    # app.include_router(client_router)
    # app.include_router(rewards_router)
    # app.include_router(visit_router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "success"}

    @app.get("/health/db")
    async def database_health_check(
        session: AsyncSession = Depends(get_async_session),
    ) -> dict[str, str]:
        is_connected = await check_database_connection(session)
        return {"database": "ok" if is_connected else "error"}

    @app.get("/health/redis")
    async def redis_health_check(
        redis: Redis = Depends(get_redis_client),
    ) -> dict[str, str]:
        is_connected = await check_redis_connection(redis)
        return {"redis": "ok" if is_connected else "error"}

    return app


app = create_app()
