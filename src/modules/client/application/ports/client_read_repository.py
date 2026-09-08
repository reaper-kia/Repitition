from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.client.application.read_models import ClientReadModel, ClientPageReadModel

class ClientReadRepository(ABC):
    """Порт для чтения клиентов (возвращает ReadModels, а не доменные сущности)."""
    
    @abstractmethod
    async def get_by_id(self, client_id: UUID) -> ClientReadModel | None:
        pass

    @abstractmethod
    async def list_by_club(self, club_id: UUID, limit: int, offset: int) -> ClientPageReadModel:
        pass