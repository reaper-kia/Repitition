"""Обучение антифрода (IsolationForest) на ЛЮБОМ CSV.

Запуск из папки ml_service:
    python -m training.train_anomaly
    python -m training.train_anomaly --data training/sample_regions.csv --id-column region_id

Список признаков больше не захардкожен: все числовые колонки CSV,
кроме --id-column, автоматически становятся признаками. Класс
IsolationForestDetector и так принимает feature_names из артефакта,
поэтому специфика осталась только здесь - и теперь её нет.

Медианы обучающей выборки сохраняются в артефакт: они нужны
explainability (абляция) на инференсе.
"""

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from ml_service.models.anomaly import IsolationForestDetector


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("training/sample_behaviour.csv"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/anomaly_model.joblib"))
    parser.add_argument("--id-column", type=str, default="subject_id",
                        help="Колонка-идентификатор, исключается из признаков")
    parser.add_argument("--contamination", type=float, default=0.05,
                        help="Ожидаемая доля аномалий, ставь близкой к реальной")
    args = parser.parse_args()

    frame = pd.read_csv(args.data)
    if args.id_column and args.id_column in frame.columns:
        frame = frame.drop(columns=[args.id_column])

    feature_frame = frame.select_dtypes(include="number")
    if feature_frame.empty:
        raise SystemExit("Не нашёл числовых колонок в CSV")
    feature_names = list(feature_frame.columns)

    model = IsolationForest(
        n_estimators=200,
        contamination=args.contamination,
        random_state=42,
    )
    model.fit(feature_frame.to_numpy(dtype=float))

    medians = feature_frame.median().to_dict()
    detector = IsolationForestDetector(
        model=model,
        feature_names=feature_names,
        medians=medians,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(detector.to_artifact(), args.out)

    print(f"Готово. Признаки ({len(feature_names)}): {feature_names}")
    print(f"Медианы (норма): {medians}")
    print(f"Артефакт сохранён: {args.out}")


if __name__ == "__main__":
    main()