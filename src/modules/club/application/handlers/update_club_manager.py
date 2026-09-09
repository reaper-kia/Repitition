from dataclasses import dataclass

from src.modules.club.application.commands.update_club_manager import (
    UpdateClubManagerCommand,
)
from src.modules.club.domain.entities import Club
from src.modules.club.domain.exceptions import (
    ClubNotFoundError,
    ManagerUserNotClubManagerError,
    ManagerUserNotFoundError,
)
from src.modules.users.domain.enums import Role
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class UpdateClubManagerHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: UpdateClubManagerCommand) -> Club:
        async with self.uow_factory() as uow:
            club = await uow.clubs.get_by_id(cmd.club_id)

            if club is None:
                raise ClubNotFoundError(f"Club {cmd.club_id} not found")

            user = await uow.users.get_by_id(cmd.manager_user_id)

            if user is None:
                raise ManagerUserNotFoundError(f"User {cmd.manager_user_id} not found")

            if user.role is not Role.CLUB_MANAGER:
                raise ManagerUserNotClubManagerError(
                    f"User {cmd.manager_user_id} is not a club manager"
                )

            club.assign_manager(cmd.manager_user_id)

            await uow.clubs.save(club)
            await uow.commit()

        return club
