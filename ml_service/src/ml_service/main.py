import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ml_service.config import settings
from ml_service.registry import registry
from ml_service.schemas import ModelHealth, PredictRequest, PredictResponse

logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    registry.load()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        docs_url="/docs",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Сервис жив. Всегда 200, даже без модели - это осознанно."""
        return {"status": "ok"}

    @app.get("/health/model", response_model=ModelHealth, tags=["health"])
    async def model_health() -> ModelHealth:
        """Загружена ли реальная модель. Дёргай перед демо."""
        return ModelHealth(
            model_loaded=registry.is_loaded,
            model_version=registry.version,
            fallback_enabled=settings.fallback_enabled,
            supported_tasks=registry.supported_tasks,
        )

    @app.post("/api/v1/predict", response_model=PredictResponse, tags=["ml"])
    async def predict(request: PredictRequest) -> PredictResponse:
        started = time.perf_counter()
        predictions, is_fallback = await registry.predict(request)
        latency_ms = (time.perf_counter() - started) * 1000

        logger.info(
            "predict request_id=%s task=%s subject=%s fallback=%s latency=%.1fms",
            request.request_id,
            request.task,
            request.subject_id,
            is_fallback,
            latency_ms,
        )

        return PredictResponse(
            request_id=request.request_id,
            task=request.task,
            predictions=predictions,
            model_version=registry.version if not is_fallback else "fallback-1.0.0",
            is_fallback=is_fallback,
            latency_ms=round(latency_ms, 2),
        )

    return app


app = create_app()
