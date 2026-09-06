from dataclasses import dataclass

from src.modules.visit.application.ports.visit_repository import VisitReadRepository
from src.modules.visit.application.queries.get_visit_by_id import GetVisitByIdQuery
from src.modules.visit.domain.exceptions import VisitNotFoundError


@dataclass
class GetVisitByIdQueryHandler:
    visit_read_repository: VisitReadRepository

    async def handle(self, query: GetVisitByIdQuery):
        result = await self.visit_read_repository.get_by_id(query.id)

        if result is None:
            raise VisitNotFoundError(f"Visit {query.id} not found")

        return result
