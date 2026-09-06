from dataclasses import dataclass

from src.modules.achivement.application.commands.create_achivement import CreateAchivementCommand
from src.modules.achivement.domain.entities import Achivement
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class CreateAchivementCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: CreateAchivementCommand) -> Achivement:
        entity = Achivement.create(name=cmd.name)

        async with self.uow_factory() as uow:
            # TODO: заменить uow.achivement на реальное имя атрибута,
            # которое ты добавишь в UnitOfWork (см. подсказку после генерации)
            await uow.achivement.add(entity)
            await uow.commit()

        return entity
