from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.rewards.application.commands.create_rewards import CreateRewardsCommand
from src.modules.rewards.application.handlers.create_rewards import (
    CreateRewardsCommandHandler,
)
from src.modules.rewards.application.handlers.get_rewards_by_id import (
    GetRewardsByIdQueryHandler,
)
from src.modules.rewards.application.ports.rewards_repository import (
    RewardsReadRepository,
)
from src.modules.rewards.application.queries.get_rewards_by_id import (
    GetRewardsByIdQuery,
)
from src.modules.rewards.infra.repositories import SQLAlchemyRewardsReadRepository
from src.shared.api.dependencies import get_unit_of_work_factory
from src.shared.application.mediator import Mediator
from src.shared.application.unit_of_work import UnitOfWorkFactory
from src.shared.infra.database.session import get_async_session


def get_rewards_read_repository(
    session: AsyncSession = Depends(get_async_session),
) -> RewardsReadRepository:
    return SQLAlchemyRewardsReadRepository(session)


def get_create_rewards_handler(
    uow_factory: UnitOfWorkFactory = Depends(get_unit_of_work_factory),
) -> CreateRewardsCommandHandler:
    return CreateRewardsCommandHandler(uow_factory=uow_factory)


def get_rewards_by_id_handler(
    repo: RewardsReadRepository = Depends(get_rewards_read_repository),
) -> GetRewardsByIdQueryHandler:
    return GetRewardsByIdQueryHandler(rewards_read_repository=repo)


def get_mediator(
    create_handler: CreateRewardsCommandHandler = Depends(get_create_rewards_handler),
    by_id_handler: GetRewardsByIdQueryHandler = Depends(get_rewards_by_id_handler),
) -> Mediator:
    mediator = Mediator()
    mediator.register(CreateRewardsCommand, create_handler)
    mediator.register(GetRewardsByIdQuery, by_id_handler)
    return mediator
