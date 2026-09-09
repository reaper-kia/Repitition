from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Tuple

from src.modules.visit.application.read_models import VisitReadModel

class VisitReadRepository(ABC):
    """Порт для чтения визитов (возвращает ReadModels)."""
    
    @abstractmethod
    async def get_current_by_club(self, club_id: UUID) -> List[VisitReadModel]:
        """Получить все открытые визиты в клубе (где exited_at IS NULL)."""
        pass

    @abstractmethod
    async def get_history_by_client(
        self, client_id: UUID, limit: int, offset: int
    ) -> Tuple[List[VisitReadModel], int]:
        """Получить историю визитов клиента с пагинацией. Возвращает (items, total)."""
        pass