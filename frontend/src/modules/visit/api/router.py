from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.visit.api.dependencies import get_mediator
from src.modules.visit.api.schemas import CreateVisitRequest, VisitResponse
from src.modules.visit.application.commands.create_visit import CreateVisitCommand
from src.modules.visit.application.queries.get_visit_by_id import GetVisitByIdQuery
from src.modules.visit.domain.exceptions import VisitNotFoundError
from src.shared.application.mediator import Mediator

router = APIRouter(prefix="/visits", tags=["Visit"])


@router.post("", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
async def create_visit(
    request: CreateVisitRequest,
    mediator: Mediator = Depends(get_mediator),
) -> VisitResponse:
    entity = await mediator.send(CreateVisitCommand(name=request.name))
    return VisitResponse(id=entity.id, name=entity.name)


@router.get("/{visit_id}", response_model=VisitResponse)
async def get_visit(
    visit_id: UUID,
    mediator: Mediator = Depends(get_mediator),
) -> VisitResponse:
    try:
        result = await mediator.send(GetVisitByIdQuery(id=visit_id))
    except VisitNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return VisitResponse(id=result.id, name=result.name)
