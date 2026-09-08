from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.modules.club.domain.entities import Club
from src.modules.club.domain.value_objects import ClubName, City
from src.modules.club.infra.models import ClubModel
from src.modules.club.application.ports.club_repository import ClubRepository
from src.modules.club.application.ports.club_read_repository import ClubReadRepository, ClubScope


class SQLAlchemyClubRepository(ClubRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, club: Club) -> None:
        model = ClubModel(
            id=club.id,
            name=club.name.value,
            city=club.city.value,
            manager_user_id=club.manager_user_id,
            is_active=club.is_active,
        )
        self._session.add(model)

    async def get_by_id(self, club_id: UUID) -> Club | None:
        stmt = select(ClubModel).where(ClubModel.id == club_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Club(
            id=model.id,
            name=ClubName(model.name),
            city=City(model.city),
            manager_user_id=model.manager_user_id,
            is_active=model.is_active,
        )

    async def save(self, club: Club) -> None:
        stmt = select(ClubModel).where(ClubModel.id == club.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Club not found")
        model.name = club.name.value
        model.city = club.city.value
        model.manager_user_id = club.manager_user_id
        model.is_active = club.is_active


class SQLAlchemyClubReadRepository(ClubReadRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_scope(self, club_id: UUID) -> ClubScope | None:
        stmt = select(ClubModel).where(ClubModel.id == club_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return ClubScope(
            club_id=model.id,
            is_active=model.is_active,
            manager_user_id=model.manager_user_id,
        )

    async def list_all(self) -> list[ClubScope]:
        stmt = select(ClubModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [
            ClubScope(
                club_id=m.id,
                is_active=m.is_active,
                manager_user_id=m.manager_user_id,
            )
            for m in models
        ]

    async def get_by_manager(self, user_id: UUID) -> ClubScope | None:
        stmt = select(ClubModel).where(ClubModel.manager_user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return ClubScope(
            club_id=model.id,
            is_active=model.is_active,
            manager_user_id=model.manager_user_id,
        )