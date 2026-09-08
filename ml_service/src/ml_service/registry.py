"""Реестр моделей: загрузка артефактов, маршрутизация по task, защита демо.

Три правила безопасности для КАЖДОЙ модели отдельно:
- нет файла модели      -> заглушка;
- модель бросила исключение -> заглушка;
- модель думает дольше таймаута -> заглушка.

Сломанная churn-модель не должна ломать работающий антифрод,
и наоборот: каждый артефакт грузится в своём try/except.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any

import joblib

from ml_service.config import settings
from ml_service.fallback import predict_fallback
from ml_service.schemas import Prediction, PredictRequest, TaskType

logger = logging.getLogger(__name__)


def _build_predictor(artifact: dict[str, Any]):
    """По полю predictor_type из артефакта строим нужный класс модели."""
    predictor_type = artifact.get("predictor_type")

    if predictor_type == "anomaly":
        from ml_service.models.anomaly import IsolationForestDetector

        return IsolationForestDetector.from_artifact(artifact)

    if predictor_type == "churn":
        from ml_service.models.churn import ChurnPredictor

        return ChurnPredictor.from_artifact(artifact)

    if predictor_type == "cluster":
        from ml_service.models.clustering import KMeansClusterer

        return KMeansClusterer.from_artifact(artifact)

    logger.warning("Неизвестный predictor_type=%s, артефакт пропущен", predictor_type)
    return None


class ModelRegistry:
    def __init__(self) -> None:
        self._predictors: dict[TaskType, Any] = {}
        self._versions: dict[TaskType, str] = {}
        self.load()

    def load(self) -> None:
        """Сканируем папку artifacts/*.joblib, каждый артефакт грузим изолированно."""
        self._predictors.clear()
        self._versions.clear()

        model_dir = Path(settings.model_dir)
        if not model_dir.exists():
            logger.warning("Папка моделей %s не существует - работаем на заглушке", model_dir)
            return

        for path in sorted(model_dir.glob("*.joblib")):
            try:
                artifact = joblib.load(path)
                predictor = _build_predictor(artifact)
                if predictor is None:
                    continue
                for task in predictor.supported_tasks:
                    if task in self._predictors:
                        # Коллизия: две модели на одну задачу (например, числовая
                        # и текстовая кластеризация). Оставляем первую загруженную.
                        logger.warning("Коллизия task=%s: оставляем первый загруженный", task)
                        continue
                    self._predictors[task] = predictor
                    self._versions[task] = getattr(predictor, "version", path.name)
                logger.info(
                    "Модель %s загружена, задачи: %s",
                    path.name,
                    [t.value for t in predictor.supported_tasks],
                )
            except Exception:
                logger.exception(
                    "Не удалось загрузить %s - пропускаем её, остальные модели живы",
                    path.name,
                )

    @property
    def supported_tasks(self) -> list[str]:
        return sorted(task.value for task in self._predictors)

    @property
    def model_loaded(self) -> bool:
        return bool(self._predictors)

    def health(self) -> dict[str, Any]:
        return {
            "model_loaded": self.model_loaded,
            "model_version": "; ".join(sorted(set(self._versions.values()))) or None,
            "supported_tasks": self.supported_tasks,
        }

    def predict(self, request: PredictRequest) -> tuple[list[Prediction], bool]:
        """Возвращает (предсказания, is_fallback)."""
        predictor = self._predictors.get(request.task)
        if predictor is None:
            return predict_fallback(request), True

        if not settings.fallback_enabled:
            # Заглушка выключена намеренно: исключения прорываются наружу (503).
            return predictor.predict(request), False

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(predictor.predict, request)
            try:
                return future.result(timeout=settings.predict_timeout_seconds), False
            except FuturesTimeoutError:
                logger.warning("Таймаут инференса task=%s -> заглушка", request.task)
            except Exception:
                logger.exception("Исключение в модели task=%s -> заглушка", request.task)

        return predict_fallback(request), True

    # Имена-алиасы, чтобы main.py нашёл своё привычное имя функции.
    predict_with_fallback = predict
    predict_safe = predict
    health_info = health


registry = ModelRegistry()


def get_registry() -> ModelRegistry:
    return registry


def load_registry() -> ModelRegistry:
    """Перечитать артефакты с диска (например, после переобучения)."""
    registry.load()
    return registry