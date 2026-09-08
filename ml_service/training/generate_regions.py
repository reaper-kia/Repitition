"""Генератор демо-данных регионов для кластеризации.

Намеренно закладываем 4 группы территорий, чтобы результат
кластеризации можно было проверить глазами:
  1. мегаполисы      - много населения, высокие доходы, близко к центру
  2. пригороды       - средние показатели всего
  3. сельские районы - мало населения, низкие доходы, далеко от центра
  4. промышленные    - среднее население, плохая экология

Запуск из папки ml_service:
    python -m training.generate_regions
"""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

GROUPS = [
    # name, n, population_thousands, income_index, distance_km, transport_score, ecology_index
    ("megapolis", 12, 900, 78, 12, 92, 55),
    ("suburb", 14, 150, 62, 45, 70, 68),
    ("rural", 14, 25, 38, 160, 30, 85),
    ("industrial", 12, 200, 55, 90, 55, 30),
]


def make_group(
    name: str,
    count: int,
    pop: float,
    income: float,
    dist: float,
    transport: float,
    ecology: float,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "region_id": [f"{name}-{i}" for i in range(count)],
            "population_thousands": np.clip(rng.normal(pop, pop * 0.15, count), 1, None),
            "income_index": np.clip(rng.normal(income, 6, count), 0, 100),
            "distance_to_center_km": np.clip(rng.normal(dist, dist * 0.2, count), 1, None),
            "transport_score": np.clip(rng.normal(transport, 8, count), 0, 100),
            "ecology_index": np.clip(rng.normal(ecology, 7, count), 0, 100),
        }
    )


def main() -> None:
    frames = [make_group(*group) for group in GROUPS]
    frame = pd.concat(frames, ignore_index=True).sample(frac=1.0, random_state=42)

    out = Path("training/sample_regions.csv")
    frame.to_csv(out, index=False)
    print(f"Готово: {len(frame)} территорий, групп: {len(GROUPS)}")
    print(f"Сохранено: {out}")


if __name__ == "__main__":
    main()