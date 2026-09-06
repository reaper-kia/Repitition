from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.application.ports.client_repository import (
    ClientReadRepository,
    ClientRepository,
)
from src.modules.client.application.read_models import ClientReadModel
from src.modules.client.domain.entities import Client
from src.modules.client.infra.models import ClientModel


class SQLAlchemyClientRepository(ClientRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Client | None:
        stmt = select(ClientModel).where(ClientModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def add(self, entity: Client) -> None:
        self.session.add(ClientModel(id=entity.id, name=entity.name))

    @staticmethod
    def _to_domain(model: ClientModel) -> Client:
        return Client(id=model.id, name=model.name)


class SQLAlchemyClientReadRepository(ClientReadRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> ClientReadModel | None:
        stmt = select(ClientModel.id, ClientModel.name).where(ClientModel.id == id)
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        return ClientReadModel(id=row.id, name=row.name) if row else None
