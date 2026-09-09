from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class CloseVisitCommand:
    """Команда от турникета: клиент вышел из клуба."""
    external_id: str      # По этому ID мы найдём открытый визит
    exited_at: datetime