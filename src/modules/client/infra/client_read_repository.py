from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.application.ports.client_read_repository import (
    ClientReadRepository,
)
from src.modules.client.application.read_models import (
    ClientPageReadModel,
    ClientReadModel,
)
from src.modules.client.domain.enums import (
    AcquisitionChannel,
    ClientStatus,
    MembershipType,
)
from src.modules.client.infra.models import ClientModel


class SQLAlchemyClientReadRepository(ClientReadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        client_id: UUID,
    ) -> ClientReadModel | None:
        stmt = select(ClientModel).where(ClientModel.id == client_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_read_model(model) if model is not None else None

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> ClientReadModel | None:
        stmt = select(ClientModel).where(ClientModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        return self._to_read_model(model) if model is not None else None

    async def list_by_club(
        self,
        club_id: UUID,
        limit: int,
        offset: int,
    ) -> ClientPageReadModel:
        count_stmt = (
            select(func.count())
            .select_from(ClientModel)
            .where(ClientModel.club_id == club_id)
        )
        total = await self._session.scalar(count_stmt) or 0

        stmt = (
            select(ClientModel)
            .where(ClientModel.club_id == club_id)
            .order_by(
                ClientModel.registered_at.desc(),
                ClientModel.id.asc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return ClientPageReadModel(
            items=[self._to_read_model(model) for model in models],
            total=total,
        )

    @staticmethod
    def _to_read_model(
        model: ClientModel,
    ) -> ClientReadModel:
        return ClientReadModel(
            id=model.id,
            user_id=model.user_id,
            club_id=model.club_id,
            display_name=model.display_name,
            membership_type=MembershipType(model.membership_type),
            membership_expires_at=model.membership_expires_at,
            referral_code=model.referral_code,
            referred_by_client_id=model.referred_by_client_id,
            acquisition_channel=AcquisitionChannel(model.acquisition_channel),
            status=ClientStatus(model.status),
            registered_at=model.registered_at,
        )
