"""КОНТРАКТ ML-сервиса: формат общения с бэкендом.

Правила правки (см. TASK.md, пункт 1.4):
- удалять, переименовывать, менять тип существующих полей - НЕЛЬЗЯ;
- добавлять новое поле можно, только опциональное и с дефолтом;
- добавлять значение в enum можно;
- любое изменение - сначала сообщение тимлиду, потом код.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class TaskType(StrEnum):
    RECOMMEND = "recommend"
    ANOMALY = "anomaly"
    SCORE = "score"
    CHURN = "churn"
    CLUSTER = "cluster"          # НОВОЕ (ML-04): кластеризация территорий


class FeatureContribution(BaseModel):
    """Вклад одного признака в объяснение ответа."""

    feature: str
    value: float
    normal_value: float          # медиана/среднее по обучающей выборке
    contribution: float          # 0..1, насколько признак повлиял на ответ


class Prediction(BaseModel):
    id: str
    score: float
    reason: str | None = None
    contributions: list[FeatureContribution] | None = None
    cluster_id: int | None = Field(
        default=None,
        description="Номер кластера. Заполнено только для task=cluster.",
    )


class PredictRequest(BaseModel):
    task: TaskType = TaskType.RECOMMEND
    subject_id: str
    features: dict[str, float] = Field(default_factory=dict)
    candidate_ids: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=50)


class PredictResponse(BaseModel):
    predictions: list[Prediction]
    is_fallback: bool = False
    model_version: str | None = None