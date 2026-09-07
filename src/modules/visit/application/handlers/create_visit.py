from dataclasses import dataclass

from src.modules.visit.application.commands.create_visit import CreateVisitCommand
from src.modules.visit.domain.entities import Visit
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class CreateVisitCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: CreateVisitCommand) -> Visit:
        entity = Visit.record(name=cmd.name)

        async with self.uow_factory() as uow:
            # TODO: заменить uow.visit на реальное имя атрибута,
            # которое ты добавишь в UnitOfWork (см. подсказку после генерации)
            await uow.visit.add(entity)
            await uow.commit()

        return entity
