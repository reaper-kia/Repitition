from typing import List, Tuple
from src.modules.visit.application.queries.get_client_visits_history import GetClientVisitsHistoryQuery
from src.modules.visit.application.read_models import VisitReadModel
from src.shared.application.unit_of_work import UnitOfWork

class GetClientVisitsHistoryHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, query: GetClientVisitsHistoryQuery) -> Tuple[List[VisitReadModel], int]:
        async with self._uow as uow:
            offset = (query.page - 1) * query.page_size
            
            return await uow.visits_read.get_history_by_client(
                client_id=query.client_id,
                limit=query.page_size,
                offset=offset,
            )