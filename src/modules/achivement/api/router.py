from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.achivement.api.dependencies import get_mediator
from src.modules.achivement.api.schemas import CreateAchivementRequest, AchivementResponse
from src.modules.achivement.application.commands.create_achivement import CreateAchivementCommand
from src.modules.achivement.application.queries.get_achivement_by_id import GetAchivementByIdQuery
from src.modules.achivement.domain.exceptions import AchivementNotFoundError
from src.shared.application.mediator import Mediator

router = APIRouter(prefix="/achivements", tags=["Achivement"])


@router.post("", response_model=AchivementResponse, status_code=status.HTTP_201_CREATED)
async def create_achivement(
    request: CreateAchivementRequest,
    mediator: Mediator = Depends(get_mediator),
) -> AchivementResponse:
    entity = await mediator.send(CreateAchivementCommand(name=request.name))
    return AchivementResponse(id=entity.id, name=entity.name)


@router.get("/{achivement_id}", response_model=AchivementResponse)
async def get_achivement(
    achivement_id: UUID,
    mediator: Mediator = Depends(get_mediator),
) -> AchivementResponse:
    try:
        result = await mediator.send(GetAchivementByIdQuery(id=achivement_id))
    except AchivementNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AchivementResponse(id=result.id, name=result.name)
