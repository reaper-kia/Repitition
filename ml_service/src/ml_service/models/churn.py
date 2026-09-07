"""Прогноз оттока: LogisticRegression.

Метки разметки НЕ делались руками - они выведены из данных:
пользователь считается ушедшим, если не совершал действий 14 дней
(разметка по окну неактивности). Поэтому возможно обучение с учителем.

LogisticRegression вместо чего-то сложного по двум причинам:
1. Обучается за секунду.
2. Коэффициенты модели сами по себе объяснение: положительный вес
   признака = рост риска оттока. Объяснимость получаем бесплатно,
   без абляций.

ЭТО ФАЙЛ, КОТОРЫЙ ТЫ МЕНЯЕШЬ.
"""

from typing import Any, ClassVar, Self

import numpy as np

from ml_service.schemas import (
    FeatureContribution,
    Prediction,
    PredictRequest,
    TaskType,
)

FEATURE_LABELS_RU: dict[str, str] = {
    "days_since_last_action": "Дней с последнего визита",
    "actions_last_7d": "Действий за последние 7 дней",
    "actions_prev_7d": "Действий за предыдущие 7 дней",
    "activity_trend": "Тренд активности (эта неделя / прошлая)",
    "account_age_days": "Возраст аккаунта, дней",
    "sessions_total": "Всего сессий",
}


class ChurnPredictor:
    version = "churn-logreg-1.0.0"
    supported_tasks: ClassVar[list[TaskType]] = [TaskType.CHURN]

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
            medians=artifact.get("medians"),
        )

    def to_artifact(self) -> dict[str, Any]:
        return {
            "predictor_type": "churn",
            "model": self._model,
            "feature_names": self._feature_names,
            "medians": self._medians,
        }

    def _vector_from(self, features: dict[str, Any]) -> np.ndarray:
        return np.array(
            [
                [
                    float(features.get(name, self._medians.get(name, 0.0)))
                    for name in self._feature_names
                ]
            ]
        )

    def _contribution_scores(
        self, vector: np.ndarray
    ) -> list[FeatureContribution]:
        """Вклад признака = вес модели * отклонение от нормы.

        Линейная модель - поэтому объяснение точное, а не приближённое:
        скор = сумма (вес_i * значение_i), значит каждый признак внёс
        ровно свой член суммы.
        """
        coefficients = self._model.coef_[0]
        raw: list[tuple[str, float, float, float]] = []

        for index, name in enumerate(self._feature_names):
            value = float(vector[0, index])
            normal_value = float(self._medians.get(name, 0.0))
            delta = float(coefficients[index]) * (value - normal_value)
            if delta > 0:
                raw.append((name, value, normal_value, delta))

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
        probability = float(self._model.predict_proba(vector)[0][1])
        contributions = self._contribution_scores(vector)

        if probability > 0.6 and contributions:
            top = contributions[0]
            label = FEATURE_LABELS_RU.get(top.feature, top.feature)
            reason = (
                f"Высокий риск оттока: {label} = {top.value} "
                f"(обычно около {top.normal_value})"
            )
        elif probability > 0.4:
            reason = "Активность снижается, стоит напомнить о себе"
        else:
            reason = "Пользователь активен, риск оттока низкий"

        return [
            Prediction(
                id=request.subject_id,
                score=round(probability, 4),
                reason=reason,
                contributions=contributions or None,
            )
        ]