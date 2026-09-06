from dataclasses import dataclass

from src.modules.achivement.application.ports.achivement_repository import AchivementReadRepository
from src.modules.achivement.application.queries.get_achivement_by_id import GetAchivementByIdQuery
from src.modules.achivement.domain.exceptions import AchivementNotFoundError


@dataclass
class GetAchivementByIdQueryHandler:
    achivement_read_repository: AchivementReadRepository

    async def handle(self, query: GetAchivementByIdQuery):
        result = await self.achivement_read_repository.get_by_id(query.id)

        if result is None:
            raise AchivementNotFoundError(f"Achivement {query.id} not found")

        return result
