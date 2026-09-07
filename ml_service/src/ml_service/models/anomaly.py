"""Детекция аномалий: IsolationForest + объяснимость (абляция).

ЭТО ФАЙЛ, КОТОРЫЙ ТЫ МЕНЯЕШЬ.

Признаки (8 штук, см. раздел 1 ТЗ):
- actions_per_day, avg_amount, max_amount - интенсивность и суммы
- night_activity_ratio, median_seconds_between_actions - регулярность (боты)
- unique_ip_count, account_age_days - мультиаккаунты
- win_ratio - накрутка выигрышей

Объяснимость (метод абляции):
1. Считаем базовый score со всеми признаками.
2. Каждый признак по очереди заменяем на медиану обучающей выборки
   ("а если бы этот признак был нормальным?") и пересчитываем score.
3. Насколько упал риск - настолько признак и был виноват.
4. Вклады нормируем в 0..1, берём топ-3.
"""

from typing import Any, ClassVar, Self

import numpy as np

from ml_service.schemas import (
    FeatureContribution,
    Prediction,
    PredictRequest,
    TaskType,
)

# Человекочитаемые названия признаков - уходят в reason и на фронт.
FEATURE_LABELS_RU: dict[str, str] = {
    "actions_per_day": "Частота действий (в день)",
    "avg_amount": "Средняя сумма операции",
    "max_amount": "Максимальная сумма",
    "night_activity_ratio": "Ночная активность (доля 00:00-06:00)",
    "median_seconds_between_actions": "Медианная пауза между действиями, сек",
    "unique_ip_count": "Число разных IP-адресов",
    "account_age_days": "Возраст аккаунта, дней",
    "win_ratio": "Доля выигрышей",
}


class IsolationForestDetector:
    version = "isolation-forest-2.0.0"
    supported_tasks: ClassVar[list[TaskType]] = [TaskType.ANOMALY, TaskType.SCORE]

    def __init__(
        self,
        model: Any,
        feature_names: list[str],
        medians: dict[str, float] | None = None,
    ) -> None:
        self._model = model
        self._feature_names = feature_names
        self._medians = medians or {}

    @classmethod
    def from_artifact(cls, artifact: dict[str, Any]) -> Self:
        return cls(
            model=artifact["model"],
            feature_names=artifact["feature_names"],
            medians=artifact.get("medians"),  # старые артефакты без медиан тоже грузятся
        )

    def to_artifact(self) -> dict[str, Any]:
        return {
            "predictor_type": "anomaly",
            "model": self._model,
            "feature_names": self._feature_names,
            "medians": self._medians,
        }

    def _vector_from(self, features: dict[str, Any]) -> np.ndarray:
        """Строим вектор признаков в обученном порядке.

        Отсутствующий признак заполняем медианой обучающей выборки
        (лучше, чем ноль: ноль сам по себе выглядит аномально).
        """
        return np.array(
            [
                [
                    float(
                        features.get(
                            name,
                            self._medians.get(name, 0.0),
                        )
                    )
                    for name in self._feature_names
                ]
            ]
        )

    def _score(self, vector: np.ndarray) -> float:
        """decision_function: чем МЕНЬШЕ, тем аномальнее. Переводим в 0..1."""
        raw = float(self._model.decision_function(vector)[0])
        return min(max(0.5 - raw, 0.0), 1.0)

    def _ablation_contributions(
        self, base_vector: np.ndarray, base_score: float
    ) -> list[FeatureContribution]:
        """Метод абляции: вклад признака = насколько упал риск,
        когда признак заменили на медиану (норму)."""
        raw: list[tuple[str, float, float, float]] = []  # (имя, значение, норма, дельта)

        for index, name in enumerate(self._feature_names):
            normal_value = float(self._medians.get(name, 0.0))
            ablated = base_vector.copy()
            ablated[0, index] = normal_value
            delta = base_score - self._score(ablated)  # >0 - признак поднимал риск
            if delta > 0:
                raw.append((name, float(base_vector[0, index]), normal_value, delta))

        total = sum(item[3] for item in raw)
        contributions = [
            FeatureContribution(
                feature=name,
                value=round(value, 4),
                normal_value=round(normal_value, 4),
                contribution=round(delta / total, 4) if total > 0 else 0.0,
            )
            for name, value, normal_value, delta in raw
        ]
        contributions.sort(key=lambda item: item.contribution, reverse=True)
        return contributions[:3]

    def predict(self, request: PredictRequest) -> list[Prediction]:
        vector = self._vector_from(request.features)
        score = self._score(vector)
        contributions = self._ablation_contributions(vector, score)

        # Пороги калиброваны на наших демо-данных (норма <0.45, фрод >0.6).
        # На реальных данных перекалибруй по выборке из сервиса.
        if score > 0.60 and contributions:
            top = contributions[0]
            label = FEATURE_LABELS_RU.get(top.feature, top.feature)
            reason = (
                f"Подозрительно: {label} = {top.value} "
                f"(обычно около {top.normal_value})"
            )
        elif score > 0.60:
            reason = "Поведение сильно отличается от обычного"
        elif score > 0.45:
            reason = "Есть отклонения от типичного профиля"
        else:
            reason = "Поведение в пределах нормы"

        return [
            Prediction(
                id=request.subject_id,
                score=round(score, 4),
                reason=reason,
                contributions=contributions or None,
            )
        ]