from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ClubScopeSnapshot:
    """Слепок данных о клубе из внешнего контекста (модуля Club)."""

    club_id: UUID
    is_active: bool
    manager_user_id: UUID | None


class ClubSnapshotRepository(ABC):
    """Порт для получения данных о клубе (из другого ограниченного контекста)."""

    @abstractmethod
    async def get_scope(self, club_id: UUID) -> ClubScopeSnapshot | None:
        pass
