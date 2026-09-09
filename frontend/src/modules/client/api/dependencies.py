from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.application.commands.create_client import CreateClientCommand
from src.modules.client.application.handlers.create_client import (
    CreateClientCommandHandler,
)
from src.modules.client.application.handlers.get_client_by_id import (
    GetClientByIdQueryHandler,
)
from src.modules.client.application.ports.client_repository import (
    ClientReadRepository,
)
from src.modules.client.application.queries.get_client_by_id import GetClientByIdQuery
from src.modules.client.infra.repositories import SQLAlchemyClientReadRepository
from src.shared.api.dependencies import get_unit_of_work_factory
from src.shared.application.mediator import Mediator
from src.shared.application.unit_of_work import UnitOfWorkFactory
from src.shared.infra.database.session import get_async_session


def get_client_read_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ClientReadRepository:
    return SQLAlchemyClientReadRepository(session)


def get_create_client_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> CreateClientCommandHandler:
    return CreateClientCommandHandler(uow_factory=uow_factory)


def get_client_by_id_handler(
    repo: ClientReadRepository = Depends(get_client_read_repository),
) -> GetClientByIdQueryHandler:
    return GetClientByIdQueryHandler(client_read_repository=repo)


def get_mediator(
    create_handler: CreateClientCommandHandler = Depends(get_create_client_handler),
    by_id_handler: GetClientByIdQueryHandler = Depends(get_client_by_id_handler),
) -> Mediator:
    mediator = Mediator()
    mediator.register(CreateClientCommand, create_handler)
    mediator.register(GetClientByIdQuery, by_id_handler)
    return mediator
