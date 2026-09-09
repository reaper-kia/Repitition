from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.client.api.dependencies import get_mediator
from src.modules.client.api.schemas import CreateClientRequest, ClientResponse
from src.modules.client.application.commands.create_client import CreateClientCommand
from src.modules.client.application.queries.get_client_by_id import GetClientByIdQuery
from src.modules.client.domain.exceptions import ClientNotFoundError
from src.shared.application.mediator import Mediator

router = APIRouter(prefix="/clients", tags=["Client"])


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    request: CreateClientRequest,
    mediator: Mediator = Depends(get_mediator),
) -> ClientResponse:
    entity = await mediator.send(CreateClientCommand(name=request.name))
    return ClientResponse(id=entity.id, name=entity.name)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    mediator: Mediator = Depends(get_mediator),
) -> ClientResponse:
    try:
        result = await mediator.send(GetClientByIdQuery(id=client_id))
    except ClientNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ClientResponse(id=result.id, name=result.name)
