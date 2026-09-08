"""Кластеризация: KMeans, работает на любом наборе числовых признаков.

ЭТО ФАЙЛ, КОТОРЫЙ ТЫ МЕНЯЕШЬ.

Смысл: не "предсказываем число", а "находим, на какие группы делятся
объекты по похожести". Бэкенд даёт произвольные числовые признаки
(что угодно: демография, доступность инфраструктуры, координаты) -
модель относит объект к одному из K кластеров и объясняет, чем этот
кластер отличается от среднего по выборке.

Объяснимость: для каждого кластера считаем, какие признаки у его
центра сильнее всего отклоняются от общего среднего по всем данным.
Тот же принцип, что абляция в anomaly.py, только вместо "что убрать,
чтобы стало нормально" здесь "чем этот кластер выделяется".
"""

from typing import Any, ClassVar, Self

import numpy as np

from ml_service.schemas import (
    FeatureContribution,
    Prediction,
    PredictRequest,
    TaskType,
)


class KMeansClusterer:
    version = "kmeans-1.0.0"
    supported_tasks: ClassVar[list[TaskType]] = [TaskType.CLUSTER]

    def __init__(
        self,
        feature_names: list[str],
        centroids: np.ndarray,              # (K, n_features), в СТАНДАРТИЗОВАНном виде
        feature_mean: np.ndarray,           # (n_features,) - для стандартизации на инференсе
        feature_scale: np.ndarray,          # (n_features,)
        global_mean_raw: dict[str, float],  # средние в исходных единицах, для reason
    ) -> None:
        self._feature_names = feature_names
        self._centroids = centroids
        self._mean = feature_mean
        self._scale = feature_scale
        self._global_mean_raw = global_mean_raw

    @classmethod
    def from_artifact(cls, artifact: dict[str, Any]) -> Self:
        return cls(
            feature_names=artifact["feature_names"],
            centroids=artifact["centroids"],
            feature_mean=artifact["feature_mean"],
            feature_scale=artifact["feature_scale"],
            global_mean_raw=artifact["global_mean_raw"],
        )

    def to_artifact(self) -> dict[str, Any]:
        return {
            "predictor_type": "cluster",
            "feature_names": self._feature_names,
            "centroids": self._centroids,
            "feature_mean": self._mean,
            "feature_scale": self._scale,
            "global_mean_raw": self._global_mean_raw,
        }

    def _standardize(self, raw_vector: np.ndarray) -> np.ndarray:
        """(x - mean) / scale. Обязательно: без этого признак с большим
        разбросом (например, население тысячами) забьёт собой признак
        с маленьким (например, доля в процентах), и кластеризация
        сведётся к группировке по одному этому признаку."""
        return (raw_vector - self._mean) / self._scale

    def predict(self, request: PredictRequest) -> list[Prediction]:
        raw = np.array(
            [
                float(request.features.get(name, self._global_mean_raw.get(name, 0.0)))
                for name in self._feature_names
            ]
        )
        standardized = self._standardize(raw)

        distances = np.linalg.norm(self._centroids - standardized, axis=1)
        cluster_id = int(np.argmin(distances))
        distance = float(distances[cluster_id])

        # Чем ближе к центру своего кластера, тем выше уверенность.
        # 1 / (1 + distance) даёт 1.0 в самом центре, плавно падает к 0.
        score = 1.0 / (1.0 + distance)

        contributions = self._defining_features(cluster_id)
        reason = self._reason(cluster_id, contributions)

        return [
            Prediction(
                id=request.subject_id,
                score=round(score, 4),
                reason=reason,
                contributions=contributions or None,
                cluster_id=cluster_id,
            )
        ]

    def _defining_features(self, cluster_id: int) -> list[FeatureContribution]:
        """Чем этот кластер выделяется на фоне общего среднего.

        В отличие от anomaly (абляция для ОДНОГО объекта), здесь сравниваем
        ЦЕНТР кластера с глобальным средним - вопрос не "что не так у
        этого объекта", а "чем эта группа отличается от остальных".
        """
        centroid_std = self._centroids[cluster_id]  # в стандартизованных единицах
        deviations = np.abs(centroid_std)           # отклонение от 0 = от среднего, в std

        order = np.argsort(deviations)[::-1][:3]
        total = float(deviations[order].sum()) or 1.0

        contributions = []
        for index in order:
            name = self._feature_names[index]
            centroid_raw = centroid_std[index] * self._scale[index] + self._mean[index]
            contributions.append(
                FeatureContribution(
                    feature=name,
                    value=round(float(centroid_raw), 4),
                    normal_value=round(float(self._global_mean_raw.get(name, 0.0)), 4),
                    contribution=round(float(deviations[index]) / total, 4),
                )
            )
        return contributions

    def _reason(self, cluster_id: int, contributions: list[FeatureContribution]) -> str:
        if not contributions:
            return f"Кластер {cluster_id}"
        top = contributions[0]
        direction = "выше" if top.value > top.normal_value else "ниже"
        return (
            f"Кластер {cluster_id}: {top.feature} {direction} среднего "
            f"({top.value} против {top.normal_value})"
        )   