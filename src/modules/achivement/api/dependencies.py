from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.achivement.application.commands.create_achivement import CreateAchivementCommand
from src.modules.achivement.application.handlers.create_achivement import (
    CreateAchivementCommandHandler,
)
from src.modules.achivement.application.handlers.get_achivement_by_id import (
    GetAchivementByIdQueryHandler,
)
from src.modules.achivement.application.ports.achivement_repository import (
    AchivementReadRepository,
)
from src.modules.achivement.application.queries.get_achivement_by_id import GetAchivementByIdQuery
from src.modules.achivement.infra.repositories import SQLAlchemyAchivementReadRepository
from src.shared.api.dependencies import get_unit_of_work_factory
from src.shared.application.mediator import Mediator
from src.shared.application.unit_of_work import UnitOfWorkFactory
from src.shared.infra.database.session import get_async_session


def get_achivement_read_repository(
    session: AsyncSession = Depends(get_async_session),
) -> AchivementReadRepository:
    return SQLAlchemyAchivementReadRepository(session)


def get_create_achivement_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> CreateAchivementCommandHandler:
    return CreateAchivementCommandHandler(uow_factory=uow_factory)


def get_achivement_by_id_handler(
    repo: AchivementReadRepository = Depends(get_achivement_read_repository),
) -> GetAchivementByIdQueryHandler:
    return GetAchivementByIdQueryHandler(achivement_read_repository=repo)


def get_mediator(
    create_handler: CreateAchivementCommandHandler = Depends(get_create_achivement_handler),
    by_id_handler: GetAchivementByIdQueryHandler = Depends(get_achivement_by_id_handler),
) -> Mediator:
    mediator = Mediator()
    mediator.register(CreateAchivementCommand, create_handler)
    mediator.register(GetAchivementByIdQuery, by_id_handler)
    return mediator
