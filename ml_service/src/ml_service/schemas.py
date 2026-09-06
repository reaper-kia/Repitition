"""Контракт ML-сервиса.

ВАЖНО: этот файл на хакатоне НЕ МЕНЯЕТСЯ.
Бэкенд и фронтенд пишут код против этих схем с первой минуты.
Меняется только содержимое predictor'ов, не формат запроса и ответа.

Если формат всё-таки надо расширить - добавляй ТОЛЬКО опциональные поля
со значением по умолчанию. Тогда старый код продолжит работать.
"""

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskType(StrEnum):
    """Какую задачу решаем.

    Один сервис умеет всё три - выбирается полем task в запросе.
    Под кейс хакатона почти наверняка подойдёт одна из них.
    """

    RECOMMEND = "recommend"  # что показать пользователю: топ-K объектов
    ANOMALY = "anomaly"  # насколько подозрительно поведение: 0..1
    SCORE = "score"  # произвольная оценка объекта: 0..1


class PredictRequest(BaseModel):
    """Тело запроса POST /api/v1/predict."""

    task: TaskType = Field(
        default=TaskType.RECOMMEND,
        description="Тип задачи",
    )
    subject_id: str = Field(
        description="Кому или чему предсказываем: user_id, session_id, item_id",
        examples=["4e2b1f0a-77ab-4a1e-9d4f-0f2a1b8c9d10"],
    )
    features: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Произвольные признаки. Бэкенд кладёт сюда всё, что знает. "
            "ML-сторона сама решает, что использовать, а что игнорировать."
        ),
        examples=[{"age_days": 12, "sessions": 40, "avg_bet": 150.0}],
    )
    candidate_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Для task=recommend: из чего выбирать. "
            "Если пусто - модель выбирает из всего каталога, который знает."
        ),
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Сколько результатов вернуть (для recommend)",
    )
    request_id: UUID = Field(
        default_factory=uuid4,
        description="Для сопоставления логов между сервисами",
    )


class Prediction(BaseModel):
    """Один элемент результата."""

    id: str = Field(description="ID объекта. Для anomaly/score равен subject_id")
    score: float = Field(ge=0.0, le=1.0, description="Уверенность или оценка, 0..1")
    reason: str | None = Field(
        default=None,
        description="Человекочитаемое объяснение. Показывай его в UI - жюри любит объяснимость.",
    )


class PredictResponse(BaseModel):
    """Тело ответа POST /api/v1/predict."""

    request_id: UUID
    task: TaskType
    predictions: list[Prediction]
    model_version: str = Field(description="Что реально отработало")
    is_fallback: bool = Field(
        description=(
            "True - отработала заглушка, а не модель. "
            "Бэкенд может показать данные без пометки 'AI', "
            "но демо при этом не падает."
        )
    )
    latency_ms: float


class ModelHealth(BaseModel):
    """Ответ GET /health/model."""

    model_loaded: bool
    model_version: str
    fallback_enabled: bool
    supported_tasks: list[TaskType]
