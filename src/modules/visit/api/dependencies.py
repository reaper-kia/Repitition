# src/modules/visit/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.database.session import get_async_session
from src.shared.infra.database.unit_of_work import SQLAlchemyUnitOfWork

from src.modules.visit.application.handlers.record_visit import RecordVisitHandler
from src.modules.visit.application.handlers.close_visit import CloseVisitHandler
from src.modules.visit.application.handlers.get_current_club_visits import GetCurrentClubVisitsHandler
from src.modules.visit.application.handlers.get_client_visits_history import GetClientVisitsHistoryHandler


async def get_record_visit_handler(
    session: AsyncSession = Depends(get_async_session)
) -> RecordVisitHandler:
    uow = SQLAlchemyUnitOfWork(session)
    return RecordVisitHandler(uow)


async def get_close_visit_handler(
    session: AsyncSession = Depends(get_async_session)
) -> CloseVisitHandler:
    uow = SQLAlchemyUnitOfWork(session)
    return CloseVisitHandler(uow)


async def get_current_club_visits_handler(
    session: AsyncSession = Depends(get_async_session)
) -> GetCurrentClubVisitsHandler:
    uow = SQLAlchemyUnitOfWork(session)
    return GetCurrentClubVisitsHandler(uow)


async def get_client_visits_history_handler(
    session: AsyncSession = Depends(get_async_session)
) -> GetClientVisitsHistoryHandler:
    uow = SQLAlchemyUnitOfWork(session)
    return GetClientVisitsHistoryHandler(uow)