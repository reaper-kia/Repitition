from dataclasses import dataclass

from src.modules.club.application.commands.create_club import CreateClubCommand
from src.modules.club.domain.entities import Club
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class CreateClubCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: CreateClubCommand) -> Club:
        entity = Club.create(name=cmd.name, city=cmd.city)

        async with self.uow_factory() as uow:
            # TODO: заменить uow.club на реальное имя атрибута,
            # которое ты добавишь в UnitOfWork (см. подсказку после генерации)
            await uow.club.add(entity)
            await uow.commit()

        return entity
