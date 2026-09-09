# src/modules/visit/application/queries/get_client_visits_history.py
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class GetClientVisitsHistoryQuery:
    """Запрос: история посещений конкретного клиента."""
    client_id: UUID
    page: int = 1
    page_size: int = 20