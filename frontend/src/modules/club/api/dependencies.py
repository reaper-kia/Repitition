from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.club.application.commands.create_club import CreateClubCommand
from src.modules.club.application.handlers.create_club import (
    CreateClubCommandHandler,
)
from src.modules.club.application.handlers.get_club_by_id import (
    GetClubByIdQueryHandler,
)
from src.modules.club.application.ports.club_repository import (
    ClubReadRepository,
)
from src.modules.club.application.queries.get_club_by_id import GetClubByIdQuery
from src.modules.club.infra.repositories import SQLAlchemyClubReadRepository
from src.shared.api.dependencies import get_unit_of_work_factory
from src.shared.application.mediator import Mediator
from src.shared.application.unit_of_work import UnitOfWorkFactory
from src.shared.infra.database.session import get_async_session


def get_club_read_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ClubReadRepository:
    return SQLAlchemyClubReadRepository(session)


def get_create_club_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> CreateClubCommandHandler:
    return CreateClubCommandHandler(uow_factory=uow_factory)


def get_club_by_id_handler(
    repo: ClubReadRepository = Depends(get_club_read_repository),
) -> GetClubByIdQueryHandler:
    return GetClubByIdQueryHandler(club_read_repository=repo)


def get_mediator(
    create_handler: CreateClubCommandHandler = Depends(get_create_club_handler),
    by_id_handler: GetClubByIdQueryHandler = Depends(get_club_by_id_handler),
) -> Mediator:
    mediator = Mediator()
    mediator.register(CreateClubCommand, create_handler)
    mediator.register(GetClubByIdQuery, by_id_handler)
    return mediator
