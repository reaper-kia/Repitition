from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.client.domain.entities import Client

class ClientRepository(ABC):
    """Порт для работы с доменными сущностями Client (Write)."""
    
    @abstractmethod
    async def add(self, client: Client) -> None:
        """Сохранить нового клиента."""
        pass

    @abstractmethod
    async def get_by_id(self, client_id: UUID) -> Client | None:
        """Найти клиента по ID (вернуть доменную сущность)."""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Client | None:
        """Найти клиента по user_id (для проверки уникальности)."""
        pass

    @abstractmethod
    async def get_by_referral_code(self, code: str) -> Client | None:
        """Найти клиента по реферальному коду."""
        pass