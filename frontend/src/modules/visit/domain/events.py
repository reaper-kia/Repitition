"""Доменные события Visit."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class VisitRecorded:
    """Клиент прошёл через турникет.

    Единственный получатель — Engagement. Один его обработчик двигает
    сразу три вещи: прогресс ClientChallenge, счётчик лидерборда в Redis
    и проверку ачивок.

    ТРАНСПОРТ: сейчас прямой вызов внутри того же запроса (без Kafka).
    Работа с БД (прогресс, ачивки) идёт в ТОЙ ЖЕ транзакции, что и запись
    визита; ZINCRBY в Redis — ПОСЛЕ коммита, потому что Redis не
    откатывается вместе с транзакцией.

    Форма события зафиксирована именно для того, чтобы переезд на
    Outbox/Kafka был правкой одной строки в Visit, а не переписыванием
    Engagement.
    """

    visit_id: UUID
    client_id: UUID
    club_id: UUID
    entered_at: datetime