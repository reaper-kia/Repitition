from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class VisitReadModel:
    """Плоская модель визита для отображения в API."""
    id: UUID
    external_id: str
    client_id: UUID
    club_id: UUID
    entered_at: datetime
    exited_at: datetime | None  # Если None, значит клиент ещё внутри