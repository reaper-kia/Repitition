"""Детекция аномалий: IsolationForest.

Применяется под антифрод, поиск подозрительной активности, выявление ботов.
Обучается без разметки - достаточно набора "обычного" поведения,
всё, что на него не похоже, получает высокий score.

Отсутствие разметки - главная причина брать именно этот алгоритм
на хакатоне: размечать данные будет некогда.

ЭТО ФАЙЛ, КОТОРЫЙ ТЫ МЕНЯЕШЬ.
"""

from typing import Any, ClassVar, Self

import numpy as np

from ml_service.schemas import Prediction, PredictRequest, TaskType


class IsolationForestDetector:
    version = "isolation-forest-1.0.0"
    supported_tasks: ClassVar[list[TaskType]] = [TaskType.ANOMALY, TaskType.SCORE]

    def __init__(self, model: Any, feature_names: list[str]) -> None:
        self._model = model
        self._feature_names = feature_names

    @classmethod
    def from_artifact(cls, artifact: dict[str, Any]) -> Self:
        return cls(
            model=artifact["model"],
            feature_names=artifact["feature_names"],
        )

    def to_artifact(self) -> dict[str, Any]:
        return {
            "predictor_type": "anomaly",
            "model": self._model,
            "feature_names": self._feature_names,
        }

    def predict(self, request: PredictRequest) -> list[Prediction]:
        # Порядок признаков должен совпадать с обучением - берём его
        # из артефакта, а не из порядка ключей в запросе.
        # Отсутствующий признак заполняем нулём, чтобы не падать.
        vector = np.array(
            [[float(request.features.get(name, 0.0)) for name in self._feature_names]]
        )

        # decision_function: чем МЕНЬШЕ, тем аномальнее. Обычно от -0.5 до 0.5.
        raw = float(self._model.decision_function(vector)[0])

        # Переводим в 0..1, где 1 = максимально подозрительно.
        score = min(max(0.5 - raw, 0.0), 1.0)

        # Пороги подобраны на sample_behaviour.csv: норма ~0.37, фрод ~0.65.
        # На РЕАЛЬНЫХ данных прогони несколько примеров через сервис
        # и подвинь эти числа - они всегда зависят от датасета.
        if score > 0.60:
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
            )
        ]
