"""Генератор демо-данных для антифрода.

Делает реалистичную картину: ~95% обычных пользователей и ~4-5%
с одним из трёх фродовых паттернов:

1. bot - слишком регулярный (паузы почти одинаковые), ночной,
   молодой аккаунт.
2. multiaccount - много разных IP, совсем свежий аккаунт.
3. win_abuser - нереально высокая доля выигрышей.

Запуск из папки ml_service:
    python -m training.generate_data
"""

from pathlib import Path

import numpy as np
import pandas as pd

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

rng = np.random.default_rng(42)

N_NORMAL = 2000
N_BOT = 40
N_MULTI = 40
N_WIN_ABUSER = 25


def make_normal(count: int) -> pd.DataFrame:
    avg = rng.lognormal(mean=5.7, sigma=0.5, size=count)  # ~300 руб
    return pd.DataFrame(
        {
            "actions_per_day": np.clip(rng.normal(12, 4, count), 1, None),
            "avg_amount": avg,
            "max_amount": avg * rng.uniform(2.0, 4.0, count),
            "night_activity_ratio": np.clip(rng.beta(2, 12, count), 0, 0.35),
            "median_seconds_between_actions": np.clip(
                rng.normal(180, 60, count), 20, None
            ),
            "unique_ip_count": rng.choice([1, 2], size=count, p=[0.85, 0.15]),
            "account_age_days": rng.integers(30, 900, count),
            "win_ratio": np.clip(rng.normal(0.42, 0.05, count), 0.2, 0.6),
        }
    )


def make_bot(count: int) -> pd.DataFrame:
    # Главная улика бота - пауза между действиями ПОЧТИ не гуляет.
    return pd.DataFrame(
        {
            "actions_per_day": rng.uniform(300, 600, count),
            "avg_amount": rng.uniform(50, 150, count),
            "max_amount": rng.uniform(50, 150, count),
            "night_activity_ratio": rng.uniform(0.6, 0.9, count),
            "median_seconds_between_actions": rng.normal(2.5, 0.1, count),
            "unique_ip_count": np.ones(count),
            "account_age_days": rng.integers(1, 7, count),
            "win_ratio": rng.uniform(0.48, 0.52, count),
        }
    )


def make_multiaccount(count: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "actions_per_day": rng.uniform(40, 90, count),
            "avg_amount": rng.uniform(100, 400, count),
            "max_amount": rng.uniform(300, 1200, count),
            "night_activity_ratio": rng.uniform(0.2, 0.5, count),
            "median_seconds_between_actions": rng.uniform(20, 60, count),
            "unique_ip_count": rng.integers(5, 15, count),
            "account_age_days": rng.integers(1, 10, count),
            "win_ratio": rng.uniform(0.4, 0.55, count),
        }
    )


def make_win_abuser(count: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "actions_per_day": rng.uniform(15, 40, count),
            "avg_amount": rng.uniform(500, 2000, count),
            "max_amount": rng.uniform(2000, 8000, count),
            "night_activity_ratio": rng.uniform(0.05, 0.3, count),
            "median_seconds_between_actions": rng.uniform(60, 300, count),
            "unique_ip_count": rng.choice([1, 2], size=count, p=[0.8, 0.2]),
            "account_age_days": rng.integers(10, 200, count),
            "win_ratio": rng.uniform(0.85, 0.98, count),
        }
    )


def main() -> None:
    parts = [
        make_normal(N_NORMAL),
        make_bot(N_BOT),
        make_multiaccount(N_MULTI),
        make_win_abuser(N_WIN_ABUSER),
    ]
    frame = pd.concat(parts, ignore_index=True)

    # subject_id пригодится бэкенду, при обучении колонка игнорируется.
    frame.insert(0, "subject_id", [f"u{index}" for index in range(len(frame))])
    frame = frame.sample(frac=1.0, random_state=42).reset_index(drop=True)

    out = Path("training/sample_behaviour.csv")
    frame.to_csv(out, index=False)

    fraud_share = (N_BOT + N_MULTI + N_WIN_ABUSER) / len(frame)
    print(f"Готово: {len(frame)} пользователей, доля фрода {fraud_share:.2%}")
    print(f"Сохранено: {out}")
    print(f"Признаки: {FEATURES}")
    print("ВАЖНО: contamination при обучении ставь близким к доле фрода.")


if __name__ == "__main__":
    main()