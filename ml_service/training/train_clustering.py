"""Обучение кластеризации на ЛЮБОМ CSV.

Запуск из папки ml_service:
    python -m training.train_clustering --data training/sample_regions.csv

В отличие от train_anomaly.py, список признаков не задан заранее:
все числовые колонки, кроме --id-column, автоматически становятся
признаками. Так скрипт работает на любом датасете без правок кода -
именно это нужно, когда реальные данные увидим только на площадке.

Число кластеров подбирается автоматически по silhouette score
в диапазоне [--k-min, --k-max], если --k не передан явно.
"""

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from ml_service.models.clustering import KMeansClusterer


def pick_k(features: np.ndarray, k_min: int, k_max: int) -> int:
    """Перебираем k, берём то, при котором объекты внутри кластера
    похожи друг на друга сильнее, чем на объекты других кластеров
    (это и есть silhouette score). Печатаем весь перебор - пригодится
    на защите объяснить, почему выбрано именно такое k."""
    best_k, best_score = k_min, -1.0
    for k in range(k_min, k_max + 1):
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(features)
        score = silhouette_score(features, labels)
        print(f"  k={k}: silhouette={score:.3f}")
        if score > best_score:
            best_k, best_score = k, score
    print(f"Выбрано k={best_k} (silhouette={best_score:.3f})")
    return best_k


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("training/sample_regions.csv"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/cluster_model.joblib"))
    parser.add_argument("--id-column", type=str, default=None,
                        help="Колонка-идентификатор, исключается из признаков")
    parser.add_argument("--k", type=int, default=None,
                        help="Число кластеров. Не задано - подбирается автоматически")
    parser.add_argument("--k-min", type=int, default=3)
    parser.add_argument("--k-max", type=int, default=8)
    args = parser.parse_args()

    frame = pd.read_csv(args.data)
    if args.id_column:
        frame = frame.drop(columns=[args.id_column])

    feature_frame = frame.select_dtypes(include="number")
    if feature_frame.empty:
        raise SystemExit("Не нашёл числовых колонок в CSV")
    feature_names = list(feature_frame.columns)

    global_mean_raw = feature_frame.mean().to_dict()
    mean = feature_frame.mean().to_numpy()
    scale = feature_frame.std().replace(0, 1).to_numpy()  # защита от деления на 0
    standardized = (feature_frame.to_numpy(dtype=float) - mean) / scale

    k = args.k or pick_k(standardized, args.k_min, args.k_max)
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    kmeans.fit(standardized)

    clusterer = KMeansClusterer(
        feature_names=feature_names,
        centroids=kmeans.cluster_centers_,
        feature_mean=mean,
        feature_scale=scale,
        global_mean_raw=global_mean_raw,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clusterer.to_artifact(), args.out)

    print(f"Готово. Признаки: {feature_names}")
    print(f"Кластеров: {k}, объектов: {len(feature_frame)}")
    print(f"Артефакт сохранён: {args.out}")


if __name__ == "__main__":
    main()