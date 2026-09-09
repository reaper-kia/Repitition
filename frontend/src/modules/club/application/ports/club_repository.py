from typing import Protocol
from uuid import UUID

from src.modules.club.application.read_models import ClubReadModel
from src.modules.club.domain.entities import Club


class ClubRepository(Protocol):
    async def get_by_id(self, id: UUID) -> Club | None: ...

    async def add(self, entity: Club) -> None: ...


class ClubReadRepository(Protocol):
    async def get_by_id(self, id: UUID) -> ClubReadModel | None: ...
