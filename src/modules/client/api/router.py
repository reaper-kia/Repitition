from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.modules.auth.api.actor import RequestActor
from src.modules.auth.api.dependencies import get_current_actor
from src.modules.client.api.dependencies import (
    get_client_by_id_handler,
    get_client_by_user_id_handler,
    get_register_client_handler,
    list_clients_by_club_handler,
)
from src.modules.client.api.schemas import (
    ClientResponse,
    RegisterClientRequest,
    client_read_model_to_response,
    client_to_response,
)
from src.modules.client.application.commands.create_client import CreateClientCommand
from src.modules.client.application.queries.get_client_by_id import (
    GetClientByIdQuery,
    GetClientByUserIdQuery,
)
from src.modules.client.application.queries.list_clients import (
    ListClientsByClubQuery,
)
from src.modules.client.domain.exceptions import (
    AccessDeniedError,
    ClientAlreadyExistsError,
    ClientNotFoundError,
    ClubInactiveError,
    InvalidReferralCodeError,
    SelfReferralError,
)

router = APIRouter(tags=["Clients"])


@router.post(
    "/api/v1/clients",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация клиента",
)
async def register_client(
    data: RegisterClientRequest,
    actor: RequestActor = Depends(get_current_actor),
    handler=Depends(get_register_client_handler),
):
    cmd = CreateClientCommand(
        user_id=actor.user_id,
        club_id=data.club_id,
        display_name=actor.name,
        membership_type=data.membership_type,
        referral_code=data.referral_code,
    )
    try:
        client = await handler.handle(cmd)
        return client_to_response(client)
    except ClientAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except (ClubInactiveError, InvalidReferralCodeError, SelfReferralError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.get(
    "/api/v1/clients/me",
    response_model=ClientResponse,
    summary="Получить профиль текущего клиента",
)
async def get_my_client(
    actor: RequestActor = Depends(get_current_actor),
    handler=Depends(get_client_by_user_id_handler),
):
    query = GetClientByUserIdQuery(
        user_id=actor.user_id,
        actor_user_id=actor.user_id,
        actor_role=actor.role,
    )
    try:
        client = await handler.handle(query)
        return client_read_model_to_response(client)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/api/v1/clients/{client_id}",
    response_model=ClientResponse,
    summary="Получить профиль клиента по ID",
)
async def get_client_by_id(
    client_id: UUID,
    actor: RequestActor = Depends(get_current_actor),
    handler=Depends(get_client_by_id_handler),
):
    query = GetClientByIdQuery(
        client_id=client_id,
        actor_user_id=actor.user_id,
        actor_role=actor.role,
    )
    try:
        client = await handler.handle(query)
        return client_read_model_to_response(client)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except AccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get(
    "/api/v1/clubs/{club_id}/clients",
    response_model=list[ClientResponse],
    summary="Получить список клиентов клуба",
)
async def list_club_clients(
    club_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: RequestActor = Depends(get_current_actor),
    handler=Depends(list_clients_by_club_handler),
):
    query = ListClientsByClubQuery(
        club_id=club_id,
        page=page,
        page_size=page_size,
        actor_user_id=actor.user_id,
        actor_role=actor.role,
    )
    try:
        page_result = await handler.handle(query)
        return [client_read_model_to_response(c) for c in page_result.items]
    except AccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
