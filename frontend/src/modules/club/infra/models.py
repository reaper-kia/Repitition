import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infra.database.base import Base


class ClubModel(Base):
    __tablename__ = "clubs"
    # TODO: если модуль живёт в отдельной схеме - __table_args__ = {"schema": "..."}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
