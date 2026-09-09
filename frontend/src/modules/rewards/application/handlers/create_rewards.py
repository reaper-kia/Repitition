from dataclasses import dataclass

from src.modules.rewards.application.commands.create_rewards import CreateRewardsCommand
from src.modules.rewards.domain.entities import Rewards
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class CreateRewardsCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: CreateRewardsCommand) -> Rewards:
        entity = Rewards.create(name=cmd.name)

        async with self.uow_factory() as uow:
            # TODO: заменить uow.rewards на реальное имя атрибута,
            # которое ты добавишь в UnitOfWork (см. подсказку после генерации)
            await uow.rewards.add(entity)
            await uow.commit()

        return entity
