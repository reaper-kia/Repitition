from dataclasses import dataclass
from src.modules.club.domain.entities import Club
from src.modules.club.domain.exceptions import ClubNotFoundError, ManagerUserNotFoundError, ManagerUserNotClubManagerError
from src.modules.club.application.ports.club_repository import ClubRepository
from src.modules.users.application.ports.user_repository import UserRepository
from src.shared.application.unit_of_work import UnitOfWork
from src.modules.club.application.commands.update_club_manager import UpdateClubManagerCommand


@dataclass
class UpdateClubManagerHandler:
    uow: UnitOfWork
    user_repo: UserRepository

    async def handle(self, cmd: UpdateClubManagerCommand) -> Club:
        async with self.uow:
            club = await self.uow.clubs.get_by_id(cmd.club_id)
            if club is None:
                raise ClubNotFoundError(f"Club {cmd.club_id} not found")
            user = await self.user_repo.get_by_id(cmd.manager_user_id)
            if user is None:
                raise ManagerUserNotFoundError(f"User {cmd.manager_user_id} not found")
            if not user.is_club_manager:
                raise ManagerUserNotClubManagerError(f"User {cmd.manager_user_id} is not a club manager")
            club.assign_manager(cmd.manager_user_id)
            await self.uow.clubs.save(club)
            await self.uow.commit()
        return club