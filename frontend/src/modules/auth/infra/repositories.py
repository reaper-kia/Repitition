from sqlalchemy import select

from src.modules.auth.application.ports.auth_user_repository import AuthUserRepository

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.read_models import AuthUserReadModel
from src.modules.users.infra.models import UserModel


class SQLAlchemyAuthUserRepository(AuthUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> AuthUserReadModel | None:
        stmt = select(UserModel.email, UserModel.id, UserModel.password_hash).where(
            UserModel.email == email
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()

        if row is None:
            return None

        return AuthUserReadModel(
            id=row.id,
            email=row.email,
            password_hash=row.password_hash,
        )
