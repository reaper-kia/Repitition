"""Тесты кластеризации (ML-04).

Проверяем на sample_regions.csv, где группы заложены намеренно:
модель должна их найти и разнести разные группы по разным кластерам.
"""

import os
import subprocess
import sys
from pathlib import Path

import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from ml_service.main import app
from ml_service.models.clustering import KMeansClusterer
from ml_service.schemas import PredictRequest, TaskType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # чтобы импортировался пакет training

from training.train_clustering import pick_k  # noqa: E402

REGIONS_CSV = ROOT / "training" / "sample_regions.csv"
CLUSTER_ARTIFACT = ROOT / "artifacts" / "cluster_model.joblib"

MEGAPOLIS = {
    "population_thousands": 950.0,
    "income_index": 80.0,
    "distance_to_center_km": 10.0,
    "transport_score": 95.0,
    "ecology_index": 55.0,
}
RURAL = {
    "population_thousands": 20.0,
    "income_index": 35.0,
    "distance_to_center_km": 170.0,
    "transport_score": 28.0,
    "ecology_index": 88.0,
}


def _standardized_regions() -> tuple[list[str], "pd.DataFrame"]:
    frame = pd.read_csv(REGIONS_CSV)
    if "region_id" in frame.columns:
        frame = frame.drop(columns=["region_id"])
    feature_frame = frame.select_dtypes(include="number")
    return list(feature_frame.columns), feature_frame


@pytest.fixture(scope="module")
def trained_clusterer() -> KMeansClusterer:
    """Обучаем модель прямо в тестах, если артефакта ещё нет."""
    if not CLUSTER_ARTIFACT.exists():
        env = {**os.environ, "PYTHONPATH": "src"}
        subprocess.run(
            [
                sys.executable, "-m", "training.train_clustering",
                "--data", str(REGIONS_CSV), "--id-column", "region_id",
            ],
            cwd=ROOT,
            check=True,
            env=env,
        )
    return KMeansClusterer.from_artifact(joblib.load(CLUSTER_ARTIFACT))


def _predict(clusterer: KMeansClusterer, features: dict, subject: str = "x"):
    request = PredictRequest(task=TaskType.CLUSTER, subject_id=subject, features=features)
    return clusterer.predict(request)[0]


def test_pick_k_finds_planted_groups() -> None:
    """На данных с 4 заложенными группами pick_k находит близкое k."""
    _, feature_frame = _standardized_regions()
    features = feature_frame.to_numpy(dtype=float)
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale == 0] = 1
    standardized = (features - mean) / scale

    k = pick_k(standardized, 3, 8)
    assert 3 <= k <= 5


def test_same_group_same_cluster(trained_clusterer: KMeansClusterer) -> None:
    """Два объекта из одной заложенной группы -> один cluster_id."""
    neighbour = dict(MEGAPOLIS)
    neighbour["population_thousands"] = 880.0
    neighbour["income_index"] = 76.0

    assert _predict(trained_clusterer, MEGAPOLIS).cluster_id == _predict(
        trained_clusterer, neighbour
    ).cluster_id


def test_different_groups_different_clusters(trained_clusterer: KMeansClusterer) -> None:
    """Мегаполис и село - разные кластеры."""
    assert _predict(trained_clusterer, MEGAPOLIS).cluster_id != _predict(
        trained_clusterer, RURAL
    ).cluster_id


def test_score_in_range(trained_clusterer: KMeansClusterer) -> None:
    assert 0.0 <= _predict(trained_clusterer, MEGAPOLIS).score <= 1.0


def test_missing_feature_does_not_crash(trained_clusterer: KMeansClusterer) -> None:
    """Нет одного признака - подставляется среднее, запрос не падает."""
    incomplete = dict(MEGAPOLIS)
    incomplete.pop("ecology_index")
    assert _predict(trained_clusterer, incomplete).cluster_id is not None


def test_contributions_sorted_desc(trained_clusterer: KMeansClusterer) -> None:
    contributions = _predict(trained_clusterer, MEGAPOLIS).contributions or []
    assert len(contributions) > 0
    values = [c.contribution for c in contributions]
    assert values == sorted(values, reverse=True)


def test_health_reports_cluster_task() -> None:
    """После обучения /health/model показывает cluster в поддержанных задачах."""
    if not CLUSTER_ARTIFACT.exists():
        pytest.skip("артефакт кластеризации не обучен")
    with TestClient(app) as client:
        body = client.get("/health/model").json()
    assert "cluster" in body.get("supported_tasks", [])