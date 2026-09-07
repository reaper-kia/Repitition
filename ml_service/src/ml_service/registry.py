"""Загрузка моделей и безопасный вызов инференса.

Три правила безопасности (сохранены для КАЖДОЙ модели отдельно):
1. Сервис стартует даже если моделей нет.
2. Любое исключение внутри модели -> заглушка, а не 500.
3. Инференс дольше таймаута -> заглушка, а не зависшее демо.

Этап 3: реестр стал мультимодельным. MODEL_PATH - теперь папка
(artifacts/), реестр сканирует все *.joblib, читает supported_tasks
каждого артефакта и строит маршрутизацию task -> predictor.
Сломанная churn-модель не ломает работающий антифрод: каждый
артефакт грузится в своём try, ошибки изолированы.
"""

import asyncio
import logging
from typing import Any, Protocol

import joblib

from ml_service.config import settings
from ml_service.fallback import FALLBACK_VERSION, predict_fallback
from ml_service.schemas import Prediction, PredictRequest, TaskType

logger = logging.getLogger(__name__)


class Predictor(Protocol):
    """Интерфейс, которому должна соответствовать любая твоя модель."""

    version: str
    supported_tasks: list[TaskType]

    def predict(self, request: PredictRequest) -> list[Prediction]: ...


def _build_predictor(artifact: dict[str, Any]) -> Predictor:
    """Создаёт predictor по полю predictor_type из артефакта."""
    predictor_type = artifact["predictor_type"]

    if predictor_type == "recommender":
        from ml_service.models.recommender import CosineRecommender

        return CosineRecommender.from_artifact(artifact)
    if predictor_type == "anomaly":
        from ml_service.models.anomaly import IsolationForestDetector

        return IsolationForestDetector.from_artifact(artifact)
    if predictor_type == "churn":
        from ml_service.models.churn import ChurnPredictor

        return ChurnPredictor.from_artifact(artifact)

    raise ValueError(f"Неизвестный predictor_type: {predictor_type}")


class ModelRegistry:
    def __init__(self) -> None:
        # Маршрутизация: тип задачи -> модель, которая её обслуживает.
        self._predictors: dict[TaskType, Predictor] = {}

    @property
    def is_loaded(self) -> bool:
        return bool(self._predictors)

    @property
    def version(self) -> str:
        if not self._predictors:
            return FALLBACK_VERSION
        versions = sorted({p.version for p in self._predictors.values()})
        return "+".join(versions)

    @property
    def supported_tasks(self) -> list[TaskType]:
        if self._predictors:
            return list(self._predictors)
        return list(TaskType)

    def load(self) -> None:
        """Вызывается один раз на старте приложения.

        Никогда не бросает исключение наружу - иначе контейнер
        уйдёт в рестарт-луп посреди хакатона.
        """
        if not settings.model_dir.exists():
            logger.warning(
                "Папка артефактов %s не найдена. Работаем на заглушке. "
                "Обучи модели: python -m training.train_anomaly, "
                "python -m training.train_churn",
                settings.model_dir,
            )
            return

        artifact_paths = sorted(settings.model_dir.glob("*.joblib"))
        if not artifact_paths:
            logger.warning(
                "В %s нет ни одного .joblib. Работаем на заглушке.",
                settings.model_dir,
            )
            return

        for path in artifact_paths:
            # Каждый артефакт грузится изолированно: битый файл
            # не мешает соседним моделям подняться.
            try:
                artifact: dict[str, Any] = joblib.load(path)
                predictor = _build_predictor(artifact)
            except Exception:
                logger.exception("Не удалось загрузить %s, пропускаем", path)
                continue

            for task in predictor.supported_tasks:
                self._predictors.setdefault(task, predictor)
            logger.info(
                "Загружен %s (%s) -> задачи %s",
                path.name,
                predictor.version,
                [task.value for task in predictor.supported_tasks],
            )

        if self._predictors:
            logger.info(
                "Реестр готов. Задачи: %s",
                [task.value for task in self._predictors],
            )

    async def predict(self, request: PredictRequest) -> tuple[list[Prediction], bool]:
        """Возвращает (предсказания, is_fallback)."""
        predictor = self._predictors.get(request.task)
        if predictor is None:
            logger.warning(
                "Задача %s не обслуживается ни одной моделью, отдаём заглушку",
                request.task,
            )
            return predict_fallback(request), True

        try:
            predictions = await asyncio.wait_for(
                asyncio.to_thread(predictor.predict, request),
                timeout=settings.predict_timeout_seconds,
            )
        except TimeoutError:
            logger.warning("Инференс превысил таймаут, отдаём заглушку")
            return predict_fallback(request), True
        # Predictor является подключаемым кодом; его сбой переводит сервис на fallback.
        except Exception:
            logger.exception("Ошибка внутри модели, отдаём заглушку")
            return predict_fallback(request), True

        if not predictions:
            return predict_fallback(request), True

        return predictions, False


registry = ModelRegistry()