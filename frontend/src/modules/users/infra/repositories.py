from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.application.ports.user_repository import (
    UserReadRepository,
    UserRepository,
)
from src.modules.users.application.read_models import UserReadModel
from src.modules.users.domain.entities import User
from src.modules.users.domain.value_objects import Email, UserName
from src.modules.users.infra.models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: Email) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.value)
        result = await self.session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if not user_model:
            return None

        return self._to_domain(user_model)

    async def get_by_id(self, id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == id)
        result = await self.session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if not user_model:
            return None

        return self._to_domain(user_model)

    async def add(self, user: User) -> None:
        user_model = UserModel(
            id=user.id,
            name=user.name.value,
            email=user.email.value,
            password_hash=user.password_hash,
            is_admin=user.is_admin,
        )
        self.session.add(user_model)

    @staticmethod
    def _to_domain(
        user_model: UserModel,
    ) -> User:
        return User(
            id=user_model.id,
            name=UserName(user_model.name),
            email=Email(user_model.email),
            password_hash=user_model.password_hash,
            is_admin=user_model.is_admin,
        )


class SQLAlchemyUserReadRepository(UserReadRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> UserReadModel | None:
        stmt = select(
            UserModel.id, UserModel.name, UserModel.email, UserModel.is_admin
        ).where(UserModel.id == id)
        result = await self.session.execute(stmt)
        user_model = result.one_or_none()

        if not user_model:
            return None

        return UserReadModel(
            id=user_model.id,
            name=user_model.name,
            email=user_model.email,
            is_admin=user_model.is_admin,
        )
