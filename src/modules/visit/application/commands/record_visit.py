from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class RecordVisitCommand:
    """Команда от турникета: клиент вошёл в клуб."""
    external_id: str      # Уникальный ID прохода из системы турникетов
    client_id: UUID
    club_id: UUID
    entered_at: datetime