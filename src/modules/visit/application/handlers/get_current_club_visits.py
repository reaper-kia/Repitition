from typing import List
from src.modules.visit.application.queries.get_current_club_visits import GetCurrentClubVisitsQuery
from src.modules.visit.application.read_models import VisitReadModel
from src.shared.application.unit_of_work import UnitOfWork

class GetCurrentClubVisitsHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, query: GetCurrentClubVisitsQuery) -> List[VisitReadModel]:
        async with self._uow as uow:
            return await uow.visits_read.get_current_by_club(query.club_id)