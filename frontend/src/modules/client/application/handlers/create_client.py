from dataclasses import dataclass

from src.modules.client.application.commands.create_client import CreateClientCommand
from src.modules.client.domain.entities import Client
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class CreateClientCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: CreateClientCommand) -> Client:
        entity = Client.create(name=cmd.name)

        async with self.uow_factory() as uow:
            # TODO: заменить uow.client на реальное имя атрибута,
            # которое ты добавишь в UnitOfWork (см. подсказку после генерации)
            await uow.client.add(entity)
            await uow.commit()

        return entity
