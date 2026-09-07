"""Тесты контракта.

Смысл: они проверяют, что сервис отвечает в нужном формате
ДАЖЕ БЕЗ ОБУЧЕННОЙ МОДЕЛИ. Если эти тесты зелёные - бэкенд
может интегрироваться, пока ты ещё возишься с моделью.

Запуск: pytest
"""

from fastapi.testclient import TestClient

from ml_service.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_health_reports_state() -> None:
    with TestClient(app) as client:
        response = client.get("/health/model")
    assert response.status_code == 200
    body = response.json()
    assert "model_loaded" in body
    assert "model_version" in body


def test_predict_works_without_model() -> None:
    """Ключевой тест. Без артефакта сервис обязан отвечать заглушкой."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/predict",
            json={
                "task": "recommend",
                "subject_id": "u1",
                "candidate_ids": ["item-1", "item-2", "item-3"],
                "top_k": 2,
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body["predictions"]) == 2
    assert all(0.0 <= p["score"] <= 1.0 for p in body["predictions"])


def test_predict_is_deterministic() -> None:
    """Один и тот же запрос даёт один и тот же ответ.

    Иначе на демо цифры прыгают при обновлении страницы.
    """
    payload = {"task": "anomaly", "subject_id": "u42", "features": {"x": 1}}
    with TestClient(app) as client:
        first = client.post("/api/v1/predict", json=payload).json()
        second = client.post("/api/v1/predict", json=payload).json()
    assert first["predictions"] == second["predictions"]


def test_predict_rejects_bad_top_k() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/predict",
            json={"subject_id": "u1", "top_k": 0},
        )
    assert response.status_code == 422

def test_churn_task_works_without_model() -> None:
    """task=churn без артефакта - заглушка, как и для остальных задач."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/predict",
            json={
                "task": "churn",
                "subject_id": "u-churn",
                "features": {"days_since_last_action": 20},
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["is_fallback"] is True
    assert len(body["predictions"]) == 1


def test_contributions_field_is_optional() -> None:
    """Поле contributions опционально: заглушка отвечает без него."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/predict",
            json={"task": "anomaly", "subject_id": "u1"},
        )
    body = response.json()
    assert "contributions" not in body["predictions"][0] or (
        body["predictions"][0]["contributions"] is None
    )