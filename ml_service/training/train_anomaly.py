"""Обучение детектора аномалий.

Запуск:
    python -m training.train_anomaly --data training/sample_behaviour.csv

Формат CSV: любые числовые колонки-признаки, по строке на объект.
Первая колонка subject_id игнорируется при обучении.

    subject_id,sessions_per_day,avg_amount,night_activity_ratio
    u1,3,150.0,0.1
    u2,40,9800.0,0.95

Разметка НЕ нужна. Модель сама выучит, что считать нормой,
по большинству строк. Поэтому данные должны быть преимущественно
"нормальными" - если половина выборки это фрод, ничего не выйдет.
"""

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from ml_service.models.anomaly import IsolationForestDetector


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path, default=Path("training/sample_behaviour.csv")
    )
    parser.add_argument("--out", type=Path, default=Path("artifacts/model.joblib"))
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.05,
        help="Ожидаемая доля аномалий в данных, обычно 0.01-0.1",
    )
    args = parser.parse_args()

    frame = pd.read_csv(args.data)
    feature_frame = frame.drop(columns=["subject_id"], errors="ignore")
    feature_frame = feature_frame.select_dtypes(include="number")

    if feature_frame.empty:
        raise SystemExit("Не нашёл числовых признаков в CSV")

    feature_names = list(feature_frame.columns)

    model = IsolationForest(
        n_estimators=200,
        contamination=args.contamination,
        random_state=42,
    )
    model.fit(feature_frame.to_numpy(dtype=float))

    detector = IsolationForestDetector(model=model, feature_names=feature_names)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(detector.to_artifact(), args.out)

    print(f"Готово. Признаки: {feature_names}")
    print(f"Обучено на {len(feature_frame)} строках")
    print(f"Артефакт сохранён: {args.out}")
    print("ВАЖНО: передай список признаков бэкенду - он должен слать ровно их")


if __name__ == "__main__":
    main()
