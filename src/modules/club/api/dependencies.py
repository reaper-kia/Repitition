from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infra.database.session import get_async_session
from src.shared.application.unit_of_work import UnitOfWorkFactory
from src.shared.api.dependencies import get_unit_of_work_factory
from src.modules.club.infra.repositories import SQLAlchemyClubRepository, SQLAlchemyClubReadRepository
from src.modules.club.application.ports.club_repository import ClubRepository
from src.modules.club.application.ports.club_read_repository import ClubReadRepository
from src.modules.users.infra.repositories import SQLAlchemyUserRepository
from src.modules.users.application.ports.user_repository import UserRepository

from src.modules.club.application.handlers.create_club import CreateClubHandler
from src.modules.club.application.handlers.update_club_manager import UpdateClubManagerHandler
from src.modules.club.application.handlers.list_clubs import ListClubsHandler
from src.modules.club.application.handlers.get_club_by_id import GetClubHandler


async def get_club_repository(session: AsyncSession = Depends(get_async_session)) -> ClubRepository:
    return SQLAlchemyClubRepository(session)


async def get_club_read_repository(session: AsyncSession = Depends(get_async_session)) -> ClubReadRepository:
    return SQLAlchemyClubReadRepository(session)


async def get_user_repository(session: AsyncSession = Depends(get_async_session)) -> UserRepository:
    return SQLAlchemyUserRepository(session)


async def get_create_club_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
    user_repo: UserRepository = Depends(get_user_repository),
) -> CreateClubHandler:
    return CreateClubHandler(uow_factory, user_repo)


async def get_update_club_manager_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UpdateClubManagerHandler:
    return UpdateClubManagerHandler(uow_factory, user_repo)


async def get_list_clubs_handler(
    read_repo: ClubReadRepository = Depends(get_club_read_repository),
) -> ListClubsHandler:
    return ListClubsHandler(read_repo)


async def get_get_club_handler(
    repo: ClubRepository = Depends(get_club_repository),
) -> GetClubHandler:
    return GetClubHandler(repo)