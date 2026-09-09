# src/modules/visit/infra/models.py
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infra.database.base import Base


class VisitModel(Base):
    __tablename__ = "visits"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Уникальный ID прохода из системы турникетов (защита от дублей)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    client_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    club_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Если NULL, значит клиент всё ещё внутри (визит открыт)
    exited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Составные индексы для ускорения специфичных запросов
    __table_args__ = (
        # Для быстрого поиска "кто сейчас в клубе"
        Index("ix_visits_club_id_exited_at", "club_id", "exited_at"),
        # Для быстрого поиска "история посещений клиента"
        Index("ix_visits_client_id_entered_at", "client_id", "entered_at"),
    )