from fastapi import Depends

from src.modules.club.application.handlers.create_club import CreateClubHandler
from src.modules.club.application.handlers.get_club_by_id import GetClubHandler
from src.modules.club.application.handlers.list_clubs import ListClubsHandler
from src.modules.club.application.handlers.update_club_manager import (
    UpdateClubManagerHandler,
)
from src.shared.api.dependencies import get_unit_of_work_factory
from src.shared.application.unit_of_work import UnitOfWorkFactory


def get_create_club_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> CreateClubHandler:
    return CreateClubHandler(uow_factory=uow_factory)


def get_update_club_manager_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> UpdateClubManagerHandler:
    return UpdateClubManagerHandler(uow_factory=uow_factory)


def get_list_clubs_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> ListClubsHandler:
    return ListClubsHandler(uow_factory=uow_factory)


def get_club_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> GetClubHandler:
    return GetClubHandler(uow_factory=uow_factory)
