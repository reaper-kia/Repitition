from fastapi import Depends

from src.modules.client.application.handlers.create_client import CreateClientHandler
from src.modules.client.application.handlers.get_client_by_id import (
    GetClientByIdHandler,
    GetClientByUserIdHandler,
)
from src.modules.client.application.handlers.list_clients import (
    ListClientsByClubHandler,
)
from src.shared.api.dependencies import get_unit_of_work_factory
from src.shared.application.unit_of_work import UnitOfWorkFactory


def get_register_client_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> CreateClientHandler:
    return CreateClientHandler(uow_factory=uow_factory)


def get_client_by_id_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> GetClientByIdHandler:
    return GetClientByIdHandler(uow_factory=uow_factory)


def get_client_by_user_id_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> GetClientByUserIdHandler:
    return GetClientByUserIdHandler(uow_factory=uow_factory)


def list_clients_by_club_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> ListClientsByClubHandler:
    return ListClientsByClubHandler(uow_factory=uow_factory)
