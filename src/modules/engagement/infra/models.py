from datetime import datetime
import uuid


from sqlalchemy import UUID, DateTime, Float, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from src.shared.infra.database.base import Base


class RetentionCaseModel(Base):
    __tablename__ = "retention_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    club_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    risk_score: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # 0..1, из ML или fallback
    risk_reasons: Mapped[list] = mapped_column(
        JSONB, nullable=False
    )  # list[str], причины текстом
    snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # RiskSnapshot замороженный
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # OPEN|OFFER_CREATED|DISMISSED
    decision: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # DISMISS|OFFER_DISCOUNT
    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    manager_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "uq_open_case_per_client",
            "client_id",
            unique=True,
            postgresql_where=text("status = 'OPEN'"),
        ),
    )
