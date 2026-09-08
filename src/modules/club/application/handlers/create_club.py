from dataclasses import dataclass
from src.modules.club.domain.entities import Club
from src.modules.club.domain.value_objects import ClubName, City
from src.modules.club.domain.exceptions import ManagerUserNotFoundError, ManagerUserNotClubManagerError
from src.modules.club.application.ports.club_repository import ClubRepository
from src.modules.users.application.ports.user_repository import UserRepository
from src.shared.application.unit_of_work import UnitOfWork
from src.modules.club.application.commands.create_club import CreateClubCommand


@dataclass
class CreateClubHandler:
    uow: UnitOfWork
    user_repo: UserRepository  # для проверки менеджера

    async def handle(self, cmd: CreateClubCommand) -> Club:
        # Проверка менеджера, если указан
        if cmd.manager_user_id is not None:
            user = await self.user_repo.get_by_id(cmd.manager_user_id)
            if user is None:
                raise ManagerUserNotFoundError(f"User {cmd.manager_user_id} not found")
            if not user.is_club_manager:  # предполагаем, что у User есть поле role или is_club_manager
                raise ManagerUserNotClubManagerError(f"User {cmd.manager_user_id} is not a club manager")

        club = Club.create(
            name=ClubName(cmd.name),
            city=City(cmd.city),
            manager_user_id=cmd.manager_user_id,
        )
        async with self.uow:
            await self.uow.clubs.add(club)
            await self.uow.commit()
        return club