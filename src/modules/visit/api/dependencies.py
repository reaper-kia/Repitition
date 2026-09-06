from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.visit.application.commands.create_visit import CreateVisitCommand
from src.modules.visit.application.handlers.create_visit import (
    CreateVisitCommandHandler,
)
from src.modules.visit.application.handlers.get_visit_by_id import (
    GetVisitByIdQueryHandler,
)
from src.modules.visit.application.ports.visit_repository import (
    VisitReadRepository,
)
from src.modules.visit.application.queries.get_visit_by_id import GetVisitByIdQuery
from src.modules.visit.infra.repositories import SQLAlchemyVisitReadRepository
from src.shared.api.dependencies import get_unit_of_work_factory
from src.shared.application.mediator import Mediator
from src.shared.application.unit_of_work import UnitOfWorkFactory
from src.shared.infra.database.session import get_async_session


def get_visit_read_repository(
    session: AsyncSession = Depends(get_async_session),
) -> VisitReadRepository:
    return SQLAlchemyVisitReadRepository(session)


def get_create_visit_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> CreateVisitCommandHandler:
    return CreateVisitCommandHandler(uow_factory=uow_factory)


def get_visit_by_id_handler(
    repo: VisitReadRepository = Depends(get_visit_read_repository),
) -> GetVisitByIdQueryHandler:
    return GetVisitByIdQueryHandler(visit_read_repository=repo)


def get_mediator(
    create_handler: CreateVisitCommandHandler = Depends(get_create_visit_handler),
    by_id_handler: GetVisitByIdQueryHandler = Depends(get_visit_by_id_handler),
) -> Mediator:
    mediator = Mediator()
    mediator.register(CreateVisitCommand, create_handler)
    mediator.register(GetVisitByIdQuery, by_id_handler)
    return mediator
