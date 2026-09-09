from typing import Protocol
from uuid import UUID

from src.modules.visit.application.read_models import VisitReadModel
from src.modules.visit.domain.entities import Visit


class VisitRepository(Protocol):
    async def get_by_id(self, id: UUID) -> Visit | None: ...

    async def add(self, entity: Visit) -> None: ...


class VisitReadRepository(Protocol):
    async def get_by_id(self, id: UUID) -> VisitReadModel | None: ...
