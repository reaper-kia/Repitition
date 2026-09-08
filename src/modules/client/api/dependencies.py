# src/modules/client/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.database.session import get_async_session
from src.shared.infra.database.unit_of_work import SQLAlchemyUnitOfWork

from src.modules.client.application.handlers.create_client import CreateClientHandler
from src.modules.client.application.handlers.get_client_by_id import GetClientByIdHandler, GetClientByUserIdHandler
from src.modules.client.application.handlers.list_clients import ListClientsByClubHandler


async def get_register_client_handler(
    session: AsyncSession = Depends(get_async_session)
) -> CreateClientHandler:
    uow = SQLAlchemyUnitOfWork(session)
    return CreateClientHandler(uow)

async def get_client_by_id_handler(
    session: AsyncSession = Depends(get_async_session)
) -> GetClientByIdHandler:
    uow = SQLAlchemyUnitOfWork(session)
    return GetClientByIdHandler(uow)

async def get_client_by_user_id_handler(
    session: AsyncSession = Depends(get_async_session)
) -> GetClientByUserIdHandler:
    uow = SQLAlchemyUnitOfWork(session)
    return GetClientByUserIdHandler(uow)

async def list_clients_by_club_handler(
    session: AsyncSession = Depends(get_async_session)
) -> ListClientsByClubHandler:
    uow = SQLAlchemyUnitOfWork(session)
    return ListClientsByClubHandler(uow)

def get_current_display_name() -> str:
    """
    Временная заглушка для получения имени пользователя.
    TODO: В будущем здесь должна быть логика декодирования JWT и извлечения поля 'name' или 'display_name'.
    """
    return "Test User"


def get_is_network_admin() -> bool:
    """
    Временная заглушка для проверки прав администратора сети.
    TODO: В будущем здесь должна быть логика декодирования JWT и проверки роли (например, 'role' == 'NETWORK_ADMIN').
    """
    return False