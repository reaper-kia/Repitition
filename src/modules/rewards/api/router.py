from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.rewards.api.dependencies import get_mediator
from src.modules.rewards.api.schemas import CreateRewardsRequest, RewardsResponse
from src.modules.rewards.application.commands.create_rewards import CreateRewardsCommand
from src.modules.rewards.application.queries.get_rewards_by_id import (
    GetRewardsByIdQuery,
)
from src.modules.rewards.domain.exceptions import RewardsNotFoundError
from src.shared.application.mediator import Mediator

router = APIRouter(prefix="/rewardss", tags=["Rewards"])


@router.post("", response_model=RewardsResponse, status_code=status.HTTP_201_CREATED)
async def create_rewards(
    request: CreateRewardsRequest,
    mediator: Mediator = Depends(get_mediator),
) -> RewardsResponse:
    entity = await mediator.send(CreateRewardsCommand(name=request.name))
    return RewardsResponse(id=entity.id, name=entity.name)


@router.get("/{rewards_id}", response_model=RewardsResponse)
async def get_rewards(
    rewards_id: UUID,
    mediator: Mediator = Depends(get_mediator),
) -> RewardsResponse:
    try:
        result = await mediator.send(GetRewardsByIdQuery(id=rewards_id))
    except RewardsNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RewardsResponse(id=result.id, name=result.name)
