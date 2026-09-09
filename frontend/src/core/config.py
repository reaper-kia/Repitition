from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "hackathon"
    app_env: str = "local"
    app_debug: bool = True

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    auth_access_cookie_name: str = "access_token"
    auth_cookie_httponly: bool = True
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    auth_cookie_path: str = "/"

    admin_registration_code: str

    postgres_host: str
    postgres_port: str
    postgres_db: str
    postgres_user: str
    postgres_password: str

    database_url: str

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str = "redis://redis:6379/0"

    redis_key_prefix: str = "app"

    auth_login_rate_limit: int = 5
    auth_login_rate_limit_window_seconds: int = 60
    auth_register_rate_limit: int = 3
    auth_register_rate_limit_window_seconds: int = 300

    # Дефолтный TTL кэша. Используй в новых модулях вместо своих констант.
    cache_ttl_seconds: int = 60

    kafka_bootstrap_servers: str = "kafka:9093"
    kafka_client_id: str = "app"

    kafka_events_consumer_group: str = "app.events"
    kafka_events_topic: str = "app.events.v1"
    kafka_events_dlq_topic: str = "app.events.dlq.v1"
    kafka_consumer_max_attempts: int = 3
    kafka_consumer_retry_delay_seconds: float = 1.0

    outbox_publisher_batch_size: int = 100
    outbox_publisher_poll_interval_seconds: float = 1.0

    # URL ML-сервиса. Пустая строка = ML отключён, бэкенд не должен падать.
    ml_service_url: str = "http://ml_service:8100"
    ml_request_timeout_seconds: float = 3.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore[call-arg]
