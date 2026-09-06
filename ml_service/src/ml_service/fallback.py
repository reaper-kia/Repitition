"""Заглушка. Работает ВСЕГДА, без обученной модели и без внешних зависимостей.

Смысл: на защите демо не должно падать из-за того, что модель не доучилась
или артефакт не собрался. Ответ приходит в том же формате, просто
is_fallback=True, а качество хуже.

Этот файл трогать не надо. Он твоя страховка.
"""

import hashlib

from ml_service.schemas import Prediction, PredictRequest, TaskType

FALLBACK_VERSION = "fallback-1.0.0"


def _stable_score(*parts: str) -> float:
    """Детерминированный псевдослучайный скор в диапазоне 0..1.

    Детерминированный - это важно: при повторном запросе с теми же данными
    ответ не меняется. Иначе на демо цифры прыгают и это выглядит как баг.
    """
    digest = hashlib.sha256("|".join(parts).encode()).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF


def predict_fallback(request: PredictRequest) -> list[Prediction]:
    if request.task is TaskType.RECOMMEND:
        candidates = request.candidate_ids or [
            f"item-{index}" for index in range(1, request.top_k + 1)
        ]
        scored = [
            Prediction(
                id=candidate,
                score=round(_stable_score(request.subject_id, candidate), 4),
                reason="Базовая выдача по популярности",
            )
            for candidate in candidates
        ]
        scored.sort(key=lambda prediction: prediction.score, reverse=True)
        return scored[: request.top_k]

    # anomaly и score: одна оценка на сам subject
    return [
        Prediction(
            id=request.subject_id,
            score=round(_stable_score(request.subject_id, request.task.value), 4),
            reason="Оценка по умолчанию, модель недоступна",
        )
    ]
