"""Рекомендации: item-item на косинусной близости.

Идея простая. Есть матрица "пользователь x объект" (кто с чем взаимодействовал).
Считаем, насколько объекты похожи друг на друга по тому, кто их выбирал.
Дальше: пользователю рекомендуем объекты, похожие на те, что он уже брал.

Это НЕ нейросеть и не должно ей быть. Это работает, объясняется жюри
за 20 секунд и обучается за 2 секунды. Именно то, что нужно на хакатоне.

ЭТО ФАЙЛ, КОТОРЫЙ ТЫ МЕНЯЕШЬ.
"""

from typing import Any, ClassVar, Self

import numpy as np

from ml_service.schemas import Prediction, PredictRequest, TaskType


class CosineRecommender:
    version = "cosine-recommender-1.0.0"
    supported_tasks: ClassVar[list[TaskType]] = [TaskType.RECOMMEND]

    def __init__(
        self,
        item_ids: list[str],
        similarity: np.ndarray,
        popularity: np.ndarray,
    ) -> None:
        self._item_ids = item_ids
        self._index = {item_id: i for i, item_id in enumerate(item_ids)}
        self._similarity = similarity
        self._popularity = popularity

    @classmethod
    def from_artifact(cls, artifact: dict[str, Any]) -> Self:
        return cls(
            item_ids=artifact["item_ids"],
            similarity=artifact["similarity"],
            popularity=artifact["popularity"],
        )

    def to_artifact(self) -> dict[str, Any]:
        return {
            "predictor_type": "recommender",
            "item_ids": self._item_ids,
            "similarity": self._similarity,
            "popularity": self._popularity,
        }

    def predict(self, request: PredictRequest) -> list[Prediction]:
        # Что пользователь уже брал - бэкенд кладёт это в features.
        # Ключ history жёстко зафиксирован, договорись о нём с бэкендом.
        history: list[str] = request.features.get("history", [])
        known_history = [item for item in history if item in self._index]

        if known_history:
            rows = [self._index[item] for item in known_history]
            scores = self._similarity[rows].mean(axis=0)
            reason_template = "Похоже на то, что вы уже выбирали"
        else:
            # Холодный старт: новому пользователю показываем популярное.
            # Это нормальное поведение, а не костыль - так делают все.
            scores = self._popularity
            reason_template = "Популярно у других пользователей"

        candidates = request.candidate_ids or self._item_ids
        seen = set(known_history)

        ranked: list[tuple[str, float]] = []
        for item_id in candidates:
            if item_id in seen or item_id not in self._index:
                continue
            ranked.append((item_id, float(scores[self._index[item_id]])))

        ranked.sort(key=lambda pair: pair[1], reverse=True)
        top = ranked[: request.top_k]

        if not top:
            return []

        # Нормализуем в 0..1, потому что схема требует именно этот диапазон.
        highest = max(score for _, score in top) or 1.0

        return [
            Prediction(
                id=item_id,
                score=round(min(max(score / highest, 0.0), 1.0), 4),
                reason=reason_template,
            )
            for item_id, score in top
        ]
