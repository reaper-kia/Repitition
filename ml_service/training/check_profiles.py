"""Проверка трёх фродовых профилей + отток - прямо в терминале.

Запуск из папки ml_service (модели должны быть обучены):
    python -m training.check_profiles

Печатает score, reason и топ-3 вклада признаков для каждого профиля.
Это ровно то, что ты покажешь на защите.
"""

from fastapi.testclient import TestClient

from ml_service.main import app

PROFILES = [
    (
        "anomaly",
        "Обычный пользователь",
        {
            "actions_per_day": 11,
            "avg_amount": 320.0,
            "max_amount": 900.0,
            "night_activity_ratio": 0.08,
            "median_seconds_between_actions": 175.0,
            "unique_ip_count": 1,
            "account_age_days": 400,
            "win_ratio": 0.43,
        },
    ),
    (
        "anomaly",
        "БОТ",
        {
            "actions_per_day": 550,
            "avg_amount": 100.0,
            "max_amount": 100.0,
            "night_activity_ratio": 0.8,
            "median_seconds_between_actions": 2.5,
            "unique_ip_count": 1,
            "account_age_days": 3,
            "win_ratio": 0.5,
        },
    ),
    (
        "anomaly",
        "МУЛЬТИАККАУНТ",
        {
            "actions_per_day": 70,
            "avg_amount": 250.0,
            "max_amount": 800.0,
            "night_activity_ratio": 0.35,
            "median_seconds_between_actions": 35.0,
            "unique_ip_count": 10,
            "account_age_days": 5,
            "win_ratio": 0.47,
        },
    ),
    (
        "anomaly",
        "НАКРУТЧИК ВЫИГРЫШЕЙ",
        {
            "actions_per_day": 25,
            "avg_amount": 1200.0,
            "max_amount": 6000.0,
            "night_activity_ratio": 0.1,
            "median_seconds_between_actions": 120.0,
            "unique_ip_count": 1,
            "account_age_days": 60,
            "win_ratio": 0.95,
        },
    ),
    (
        "churn",
        "Уходящий пользователь",
        {
            "days_since_last_action": 30,
            "actions_last_7d": 0,
            "actions_prev_7d": 15,
            "activity_trend": 0.0,
            "account_age_days": 200,
            "sessions_total": 80,
        },
    ),
    (
        "churn",
        "Лояльный пользователь",
        {
            "days_since_last_action": 1,
            "actions_last_7d": 20,
            "actions_prev_7d": 18,
            "activity_trend": 1.05,
            "account_age_days": 500,
            "sessions_total": 300,
        },
    ),
]


def main() -> None:
    with TestClient(app) as client:
        for task, title, features in PROFILES:
            response = client.post(
                "/api/v1/predict",
                json={"task": task, "subject_id": "demo", "features": features},
            )
            body = response.json()
            prediction = body["predictions"][0]

            print(f"\n=== {title} (task={task}) ===")
            print(f"  score:       {prediction['score']}")
            print(f"  reason:      {prediction['reason']}")
            print(f"  fallback:    {body['is_fallback']}")
            for item in prediction.get("contributions") or []:
                print(
                    f"    - {item['feature']}: {item['value']} "
                    f"(норма {item['normal_value']}), "
                    f"вклад {item['contribution']}"
                )


if __name__ == "__main__":
    main()