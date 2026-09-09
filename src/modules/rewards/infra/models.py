from datetime import date, datetime
from decimal import Decimal
import uuid

from sqlalchemy import (
    UUID,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infra.database.base import Base


class RewardBudgetModel(Base):  # Кошелек клуба на месяц
    __tablename__ = "reward_budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    club_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )  # не FK — clubs пишет B1
    budget_month: Mapped[date] = mapped_column(Date, nullable=False)  # всегда 1-е число
    revenue_base: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )  # выручка M-1, от неё считается 4%
    configured_limit: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )  # ручной потолок клуба
    reserved: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )  # заморожено под обещания
    spent: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )  # реально потрачено
    released: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )  # вернулось из отменённых броней
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # optimistic lock

    __table_args__ = (
        UniqueConstraint("club_id", "budget_month", name="uq_budget_club_month"),
        CheckConstraint("reserved >= 0 AND spent >= 0", name="ck_budget_non_negative"),
        CheckConstraint(
            "reserved + spent <= LEAST(configured_limit, revenue_base * 0.04)",
            name="ck_budget_limit",
        ),
    )


class BudgetReservationModel(Base):  # будущую награду
    __tablename__ = "budget_reservations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    budget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reward_budgets.id"), nullable=False, index=True
    )  # FK — внутри модуля, можно жёстко
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # REFERRAL | RETENTION
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )  # id клиента/кейса
    reserved_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    consumed_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )  # защита от повтора резерва
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # ACTIVE|CONSUMED|RELEASED|EXPIRED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "consumed_amount <= reserved_amount", name="ck_reservation_consumed"
        ),
    )


class DiscountGrantModel(Base):  # купон на руках клиента
    __tablename__ = "discount_grants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )  # не FK — clients пишет B2
    reservation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("budget_reservations.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    purpose: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # REFERRAL_INVITEE|REFERRAL_REFERRER|RETENTION
    applicable_purchase_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # к какой покупке применим
    source_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )  # защита от двойной выдачи
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # AVAILABLE|REDEEMED|EXPIRED|CANCELLED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    redeemed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = ()  # весь contract на source_key UNIQUE выше
