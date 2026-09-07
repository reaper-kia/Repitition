"""Контракт ML-сервиса.

Правила изменений (раздел 1.4 ТЗ):
- существующие поля не удалять, не переименовывать, не менять тип;
- новые поля — только опциональные, со значением по умолчанию;
- новые значения enum — можно.

Изменения этапов 2-3: поле Prediction.contributions (опционально,
дефолт None) и значение TaskType.CHURN. Обратная совместимость сохранена.
"""

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskType(StrEnum):
    """Какую задачу решаем."""

    RECOMMEND = "recommend"  # что показать пользователю: топ-K объектов
    ANOMALY = "anomaly"  # насколько подозрительно поведение: 0..1
    SCORE = "score"  # произвольная оценка объекта: 0..1
    CHURN = "churn"  # прогноз оттока: вероятность, что пользователь уйдёт


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


class FeatureContribution(BaseModel):
    """Вклад одного признака в итоговый скор (этап 2, объяснимость).

    Опционально: приходит только от моделей, которые умеют объяснять.
    """

    feature: str = Field(description="Имя признака (как в features запроса)")
    value: float = Field(description="Значение признака у этого пользователя")
    normal_value: float = Field(description="Медиана по обучающей выборке (норма)")
    contribution: float = Field(
        ge=0.0,
        le=1.0,
        description="Насколько признак поднял риск, 0..1 (доля от суммы вкладов)",
    )


class Prediction(BaseModel):
    """Один элемент результата."""

    id: str = Field(description="ID объекта. Для anomaly/score равен subject_id")
    score: float = Field(ge=0.0, le=1.0, description="Уверенность или оценка, 0..1")
    reason: str | None = Field(
        default=None,
        description="Человекочитаемое объяснение. Показывай его в UI - жюри любит объяснимость.",
    )
    contributions: list[FeatureContribution] | None = Field(
        default=None,
        description="Топ-3 признака, поднявших риск. None - модель не умеет объяснять.",
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