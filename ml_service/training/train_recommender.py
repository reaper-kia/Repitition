"""Обучение рекомендателя.

Запуск:
    python -m training.train_recommender --data training/sample_interactions.csv

Формат CSV (три колонки, заголовок обязателен):
    user_id,item_id,weight
    u1,item-3,1
    u1,item-7,1
    u2,item-3,2

weight - насколько сильно взаимодействие: просмотр 1, покупка 3, и так далее.
Если у тебя нет весов - ставь везде 1, работать будет.

На хакатоне данные тебе даст бэкенд из своей базы одним SQL-запросом.
Договорись об этом заранее, чтобы не ждать.
"""

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml_service.models.recommender import CosineRecommender


def build_matrix(frame: pd.DataFrame) -> tuple[list[str], np.ndarray]:
    """Строит матрицу пользователь x объект."""
    pivot = frame.pivot_table(
        index="user_id",
        columns="item_id",
        values="weight",
        aggfunc="sum",
        fill_value=0,
    )
    return list(pivot.columns), pivot.to_numpy(dtype=float)


def cosine_similarity(matrix: np.ndarray) -> np.ndarray:
    """Косинусная близость между колонками (объектами).

    Формула: cos(a, b) = (a . b) / (|a| * |b|)
    Делим на норму, чтобы популярный объект не был похож сразу на всё.
    """
    norms = np.linalg.norm(matrix, axis=0)
    norms[norms == 0] = 1.0  # защита от деления на ноль
    normalized = matrix / norms
    similarity = normalized.T @ normalized
    np.fill_diagonal(similarity, 0.0)  # объект не рекомендует сам себя
    return similarity


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path, default=Path("training/sample_interactions.csv")
    )
    parser.add_argument("--out", type=Path, default=Path("artifacts/model.joblib"))
    args = parser.parse_args()

    frame = pd.read_csv(args.data)
    required = {"user_id", "item_id", "weight"}
    missing = required - set(frame.columns)
    if missing:
        raise SystemExit(f"В CSV не хватает колонок: {sorted(missing)}")

    item_ids, matrix = build_matrix(frame)
    similarity = cosine_similarity(matrix)
    popularity = matrix.sum(axis=0)
    if popularity.max() > 0:
        popularity = popularity / popularity.max()

    model = CosineRecommender(
        item_ids=item_ids,
        similarity=similarity,
        popularity=popularity,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model.to_artifact(), args.out)

    print(f"Готово. Объектов: {len(item_ids)}, пользователей: {matrix.shape[0]}")
    print(f"Артефакт сохранён: {args.out}")
    print("Теперь перезапусти сервис: docker compose restart ml_service")


if __name__ == "__main__":
    main()
