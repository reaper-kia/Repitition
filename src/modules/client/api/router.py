# src/modules/client/api/router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID

from src.modules.client.api.schemas import (
    RegisterClientRequest,
    ClientResponse,
    client_to_response,
    client_read_model_to_response,
)
from src.modules.client.api.dependencies import (
    get_register_client_handler,
    get_client_by_id_handler,
    get_client_by_user_id_handler,
    list_clients_by_club_handler,
)
from src.modules.client.application.commands.create_client import CreateClientCommand
from src.modules.client.application.queries.get_client_by_id import GetClientByIdQuery, GetClientByUserIdQuery
from src.modules.client.application.queries.list_clients import ListClientsByClubQuery

from src.modules.client.domain.exceptions import (
    ClientAlreadyExistsError,
    ClubInactiveError,
    InvalidReferralCodeError,
    SelfReferralError,
    ClientNotFoundError,
    AccessDeniedError,
)

# ⚠️ ВАЖНО: Здесь используются заглушки для авторизации. 
# В твоем проекте нужно будет подставить реальные зависимости из модуля auth/users.
# Например: from src.modules.auth.api.dependencies import get_current_actor
# class Actor: user_id: UUID, display_name: str, is_network_admin: bool
from src.modules.auth.api.dependencies import get_current_user_id, get_current_display_name, get_is_network_admin

router = APIRouter(tags=["Clients"])


# 1. Регистрация клиента
@router.post(
    "/api/v1/clients",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация клиента"
)
async def register_client(
    data: RegisterClientRequest,
    actor_user_id: UUID = Depends(get_current_user_id),
    actor_display_name: str = Depends(get_current_display_name), # Берем имя из JWT/Identity
    handler=Depends(get_register_client_handler),
):
    cmd = CreateClientCommand(
        user_id=actor_user_id,
        club_id=data.club_id,
        display_name=actor_display_name,
        membership_type=data.membership_type,
        referral_code=data.referral_code,
    )
    try:
        client = await handler.handle(cmd)
        return client_to_response(client)
    except ClientAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (ClubInactiveError, InvalidReferralCodeError, SelfReferralError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# 2. Получить своего профиля
@router.get(
    "/api/v1/clients/me",
    response_model=ClientResponse,
    summary="Получить профиль текущего клиента"
)
async def get_my_client(
    actor_user_id: UUID = Depends(get_current_user_id),
    is_network_admin: bool = Depends(get_is_network_admin),
    handler=Depends(get_client_by_user_id_handler),
):
    query = GetClientByUserIdQuery(
        user_id=actor_user_id,
        actor_user_id=actor_user_id,
        is_network_admin=is_network_admin,
    )
    try:
        client = await handler.handle(query)
        return client_read_model_to_response(client)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# 3. Получить профиль клиента по ID
@router.get(
    "/api/v1/clients/{client_id}",
    response_model=ClientResponse,
    summary="Получить профиль клиента по ID"
)
async def get_client_by_id(
    client_id: UUID,
    actor_user_id: UUID = Depends(get_current_user_id),
    is_network_admin: bool = Depends(get_is_network_admin),
    handler=Depends(get_client_by_id_handler),
):
    query = GetClientByIdQuery(
        client_id=client_id,
        actor_user_id=actor_user_id,
        is_network_admin=is_network_admin,
    )
    try:
        client = await handler.handle(query)
        return client_read_model_to_response(client)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# 4. Список клиентов клуба (для менеджера)
@router.get(
    "/api/v1/clubs/{club_id}/clients",
    response_model=list[ClientResponse],
    summary="Получить список клиентов клуба"
)
async def list_club_clients(
    club_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor_user_id: UUID = Depends(get_current_user_id),
    is_network_admin: bool = Depends(get_is_network_admin),
    handler=Depends(list_clients_by_club_handler),
):
    query = ListClientsByClubQuery(
        club_id=club_id,
        page=page,
        page_size=page_size,
        actor_user_id=actor_user_id,
        is_network_admin=is_network_admin,
    )
    try:
        page_result = await handler.handle(query)
        return [client_read_model_to_response(client) for client in page_result.items]
    except AccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))