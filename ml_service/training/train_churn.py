"""Обучение прогноза оттока (LogisticRegression).

Метки НЕ размечались руками - они выводятся из данных:
пользователь ушёл, если не было действий 14+ дней
(разметка по окну неактивности).

Запуск из папки ml_service:
    python -m training.train_churn

Артефакт: artifacts/churn_model.joblib
"""

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

from ml_service.models.churn import ChurnPredictor

FEATURES = [
    "days_since_last_action",
    "actions_last_7d",
    "actions_prev_7d",
    "activity_trend",
    "account_age_days",
    "sessions_total",
]

CHURN_WINDOW_DAYS = 14
rng = np.random.default_rng(42)


def generate_churn_frame(count: int = 3000) -> pd.DataFrame:
    """Синтетика: у активных и уходящих разные профили активности."""
    n_active = int(count * 0.7)

    active = pd.DataFrame(
        {
            "days_since_last_action": rng.integers(0, 7, n_active),
            "actions_last_7d": rng.uniform(5, 30, n_active),
            "actions_prev_7d": rng.uniform(5, 30, n_active),
            "account_age_days": rng.integers(30, 700, count - n_active + n_active)[
                :n_active
            ],
            "sessions_total": rng.integers(20, 500, n_active),
        }
    )
    active["activity_trend"] = active["actions_last_7d"] / (
        active["actions_prev_7d"] + 1
    )
    active["churn"] = 0

    n_churn = count - n_active
    churning = pd.DataFrame(
        {
            "days_since_last_action": rng.integers(CHURN_WINDOW_DAYS, 45, n_churn),
            "actions_last_7d": rng.uniform(0, 2, n_churn),
            "actions_prev_7d": rng.uniform(5, 25, n_churn),
            "account_age_days": rng.integers(30, 700, n_churn),
            "sessions_total": rng.integers(10, 400, n_churn),
        }
    )
    churning["activity_trend"] = churning["actions_last_7d"] / (
        churning["actions_prev_7d"] + 1
    )
    churning["churn"] = 1

    return pd.concat([active, churning], ignore_index=True).sample(
        frac=1.0, random_state=42
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("artifacts/churn_model.joblib"))
    args = parser.parse_args()

    frame = generate_churn_frame()

    x = frame[FEATURES].to_numpy(dtype=float)
    y = frame["churn"].to_numpy(dtype=int)

    model = LogisticRegression(max_iter=1000)
    model.fit(x, y)

    # Качество на тех же данных - только чтобы убедиться, что модель
    # вообще выучила закономерность. На хакатоне замени на train/test split.
    report = classification_report(y, model.predict(x), output_dict=True)
    print(f"Accuracy: {report['accuracy']:.3f}")
    print(f"Precision (отток): {report['1']['precision']:.3f}")
    print(f"Recall (отток): {report['1']['recall']:.3f}")

    medians = frame[FEATURES].median().to_dict()
    predictor = ChurnPredictor(
        model=model,
        feature_names=FEATURES,
        medians=medians,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(predictor.to_artifact(), args.out)

    print(f"Готово. Признаки: {FEATURES}")
    print(f"Медианы (норма): {medians}")
    print(f"Артефакт сохранён: {args.out}")
    print(f"Веса модели (объяснимость): {dict(zip(FEATURES, model.coef_[0].round(3)))}")


if __name__ == "__main__":
    main()