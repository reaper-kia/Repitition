"""Обучение детектора аномалий (IsolationForest).

Запуск из папки ml_service:
    python -m training.train_anomaly

Артефакт: artifacts/anomaly_model.joblib
Внутри: модель, порядок признаков, медианы обучающей выборки
(нужны для объяснимости - это "норма", от которой считаем отклонения).

Разметка НЕ нужна. Данные должны быть преимущественно "нормальными":
IsolationForest выучивает норму по большинству, остальное - аномалии.
Поэтому contamination ставим близким к реальной доле фрода (~0.04),
дефолтные 0.05 дали бы много ложных срабатываний.
"""

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from ml_service.models.anomaly import IsolationForestDetector

# Целевой список признаков (согласован с бэкендом, раздел 1 ТЗ).
FEATURES = [
    "actions_per_day",
    "avg_amount",
    "max_amount",
    "night_activity_ratio",
    "median_seconds_between_actions",
    "unique_ip_count",
    "account_age_days",
    "win_ratio",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path, default=Path("training/sample_behaviour.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("artifacts/anomaly_model.joblib")
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.04,
        help="Ожидаемая доля аномалий, обычно 0.01-0.1. У нас ~4% фрода.",
    )
    args = parser.parse_args()

    frame = pd.read_csv(args.data)

    missing = [name for name in FEATURES if name not in frame.columns]
    if missing:
        raise SystemExit(f"В CSV нет признаков: {missing}")

    feature_frame = frame[FEATURES].astype(float)
    feature_names = FEATURES

    model = IsolationForest(
        n_estimators=200,
        contamination=args.contamination,
        random_state=42,
    )
    model.fit(feature_frame.to_numpy(dtype=float))

    # Медианы - "норма". Сохраняем в артефакт: объяснимость и
    # заполнение пропусков при инференсе работают от них.
    medians = feature_frame.median().to_dict()

    detector = IsolationForestDetector(
        model=model,
        feature_names=feature_names,
        medians=medians,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(detector.to_artifact(), args.out)

    print(f"Готово. Признаки: {feature_names}")
    print(f"Обучено на {len(feature_frame)} строках")
    print(f"Медианы (норма): {medians}")
    print(f"Артефакт сохранён: {args.out}")
    print("ВАЖНО: передай список признаков бэкенду - он должен слать ровно их")


if __name__ == "__main__":
    main()