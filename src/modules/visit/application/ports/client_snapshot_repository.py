from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class ClientSnapshot:
    """Слепок данных о клиенте из внешнего контекста (модуля Client)."""
    client_id: UUID
    club_id: UUID
    is_active: bool  # Например, статус абонемента (ACTIVE/EXPIRED)

class ClientSnapshotRepository(ABC):
    """Порт для получения данных о клиенте (из другого ограниченного контекста)."""
    
    @abstractmethod
    async def get_by_id(self, client_id: UUID) -> ClientSnapshot | None:
        pass