from dataclasses import dataclass

from src.modules.club.application.commands.create_club import CreateClubCommand
from src.modules.club.domain.entities import Club
from src.modules.club.domain.exceptions import (
    ManagerUserNotClubManagerError,
    ManagerUserNotFoundError,
)
from src.modules.club.domain.value_objects import City, ClubName
from src.modules.users.domain.enums import Role
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class CreateClubHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: CreateClubCommand) -> Club:
        name = ClubName(cmd.name)
        city = City(cmd.city)

        async with self.uow_factory() as uow:
            if cmd.manager_user_id is not None:
                user = await uow.users.get_by_id(cmd.manager_user_id)
                if user is None:
                    raise ManagerUserNotFoundError(
                        f"User {cmd.manager_user_id} not found"
                    )
                if user.role is not Role.CLUB_MANAGER:
                    raise ManagerUserNotClubManagerError(
                        f"User {cmd.manager_user_id} is not a club manager"
                    )

            club = Club.create(
                name=name,
                city=city,
                manager_user_id=cmd.manager_user_id,
            )

            await uow.clubs.add(club)
            await uow.commit()

        return club
