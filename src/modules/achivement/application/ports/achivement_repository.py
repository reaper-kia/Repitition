from typing import Protocol
from uuid import UUID

from src.modules.achivement.application.read_models import AchivementReadModel
from src.modules.achivement.domain.entities import Achivement


class AchivementRepository(Protocol):
    async def get_by_id(self, id: UUID) -> Achivement | None: ...

    async def add(self, entity: Achivement) -> None: ...


class AchivementReadRepository(Protocol):
    async def get_by_id(self, id: UUID) -> AchivementReadModel | None: ...
