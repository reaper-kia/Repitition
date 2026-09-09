from dataclasses import dataclass

from src.modules.users.application.ports.user_repository import UserReadRepository
from src.modules.users.application.queries.get_user_by_id import GetUserByIdQuery
from src.modules.users.domain.exceptions import UserNotFoundError


@dataclass
class GetUserByIdQueryHandler:
    user_read_repository: UserReadRepository

    async def handle(self, query: GetUserByIdQuery):
        result = await self.user_read_repository.get_by_id(query.id)

        if result is None:
            raise UserNotFoundError("User not found")

        return result
