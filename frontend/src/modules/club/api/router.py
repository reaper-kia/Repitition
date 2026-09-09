from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.club.api.dependencies import get_mediator
from src.modules.club.api.schemas import CreateClubRequest, ClubResponse
from src.modules.club.application.commands.create_club import CreateClubCommand
from src.modules.club.application.queries.get_club_by_id import GetClubByIdQuery
from src.modules.club.domain.exceptions import ClubNotFoundError
from src.shared.application.mediator import Mediator

router = APIRouter(prefix="/clubs", tags=["Club"])


@router.post("", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
async def create_club(
    request: CreateClubRequest,
    mediator: Mediator = Depends(get_mediator),
) -> ClubResponse:
    entity = await mediator.send(CreateClubCommand(name=request.name))
    return ClubResponse(id=entity.id, name=entity.name)


@router.get("/{club_id}", response_model=ClubResponse)
async def get_club(
    club_id: UUID,
    mediator: Mediator = Depends(get_mediator),
) -> ClubResponse:
    try:
        result = await mediator.send(GetClubByIdQuery(id=club_id))
    except ClubNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ClubResponse(id=result.id, name=result.name)
