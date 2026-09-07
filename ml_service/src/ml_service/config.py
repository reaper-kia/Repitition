from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ML Service"
    app_debug: bool = False

    # ПАПКА с артефактами моделей (этап 3: моделей стало несколько).
    # Реестр при старте сканирует все *.joblib в ней.
    # Если папка пуста - сервис ВСЁ РАВНО стартует и работает на заглушке.
    model_dir: Path = Path("artifacts")

    # Выключай только если хочешь явно увидеть 503 вместо тихой заглушки.
    # На демо всегда должно быть True.
    fallback_enabled: bool = True

    # Ограничение времени на один инференс. Если модель думает дольше -
    # отдаём заглушку. Демо не должно висеть.
    predict_timeout_seconds: float = 2.0

    host: str = "0.0.0.0"
    port: int = 8100


settings = Settings()