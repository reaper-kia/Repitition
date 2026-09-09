from abc import ABC, abstractmethod
from src.modules.visit.domain.entities import Visit

class VisitRepository(ABC):
    """Порт для работы с доменными сущностями Visit (Write)."""
    
    @abstractmethod
    async def add(self, visit: Visit) -> None:
        """Сохранить новый визит."""
        pass

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Visit | None:
        """Найти визит по external_id (для проверки идемпотентности и закрытия)."""
        pass