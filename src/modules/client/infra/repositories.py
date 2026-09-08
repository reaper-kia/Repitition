# src/modules/client/infra/repositories/client_repository.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.application.ports.client_repository import ClientRepository
from src.modules.client.domain.entities import Client
from src.modules.client.domain.enums import AcquisitionChannel, ClientStatus, MembershipType
from src.modules.client.domain.value_objects import Membership, ReferralCode
from src.modules.client.infra.models import ClientModel


class SQLAlchemyClientRepository(ClientRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, client: Client) -> None:
        model = self._to_model(client)
        self._session.add(model)

    async def get_by_id(self, client_id: UUID) -> Client | None:
        stmt = select(ClientModel).where(ClientModel.id == client_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_user_id(self, user_id: UUID) -> Client | None:
        stmt = select(ClientModel).where(ClientModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_referral_code(self, code: str) -> Client | None:
        stmt = select(ClientModel).where(ClientModel.referral_code == code)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    # --- Мапперы ---
    @staticmethod
    def _to_model(client: Client) -> ClientModel:
        return ClientModel(
            id=client.id,
            user_id=client.user_id,
            club_id=client.club_id,
            display_name=client.display_name,
            membership_type=client.membership.type.value,
            membership_expires_at=client.membership.expires_at,
            referral_code=client.referral_code.value,
            referred_by_client_id=client.referred_by_client_id,
            acquisition_channel=client.acquisition_channel.value,
            status=client.status.value,
            registered_at=client.registered_at,
        )

    @staticmethod
    def _to_domain(model: ClientModel) -> Client:
        return Client(
            id=model.id,
            user_id=model.user_id,
            club_id=model.club_id,
            display_name=model.display_name,
            membership=Membership(
                type=MembershipType(model.membership_type),
                expires_at=model.membership_expires_at,
            ),
            referral_code=ReferralCode(value=model.referral_code),
            referred_by_client_id=model.referred_by_client_id,
            acquisition_channel=AcquisitionChannel(model.acquisition_channel),
            status=ClientStatus(model.status),
            registered_at=model.registered_at,
        )