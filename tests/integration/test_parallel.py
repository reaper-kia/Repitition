import asyncio
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import insert, select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.modules.rewards.application.commands.consume_reservation import ConsumeReservationCommand
from src.modules.rewards.application.handlers.consume_reservation import ConsumeReservationCommandHandler
from src.modules.rewards.application.commands.reserve_budget import ReserveBudgetCommand
from src.modules.rewards.application.handlers.reserve_budget import (
    ReserveBudgetCommandHandler,
)
from src.modules.rewards.infra.models import (
    DiscountGrantModel,
    RewardBudgetModel,
    BudgetReservationModel,
)
from src.shared.infra.database.unit_of_work import SQLAlchemyUnitOfWork

pytestmark = pytest.mark.integration


async def test_two_parallel_reservations_one_wins(engine):
    club_id = uuid.uuid4()
    month = date(2026, 9, 1)

    # бюджет с лимитом 40 000 (revenue_base 1 000 000 * 4%)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        await s.execute(
            insert(RewardBudgetModel).values(
                id=uuid.uuid4(),
                club_id=club_id,
                budget_month=month,
                revenue_base=Decimal("1000000.00"),
                configured_limit=Decimal("100000.00"),
                reserved=Decimal("0"),
                spent=Decimal("0"),
                released=Decimal("0"),
                version=0,
            )
        )
        await s.commit()

    # фабрика UoW поверх нашего engine — каждый хендлер откроет свою сессию
    def uow_factory():
        return SQLAlchemyUnitOfWork(maker)

    handler = ReserveBudgetCommandHandler(uow_factory=uow_factory)

    # две команды, каждая по 30 000: по отдельности влезает, вместе — нет
    cmd_a = ReserveBudgetCommand(
        club_id=club_id, source_type="REFERRAL",
        source_id=uuid.uuid4(), amount=Decimal("30000.00"),
        idempotency_key=f"a:{uuid.uuid4()}",
    )
    cmd_b = ReserveBudgetCommand(
        club_id=club_id, source_type="REFERRAL",
        source_id=uuid.uuid4(), amount=Decimal("30000.00"),
        idempotency_key=f"b:{uuid.uuid4()}",
    )

    # запускаем оба ОДНОВРЕМЕННО
    result_a, result_b = await asyncio.gather(
        handler.handle(cmd_a),
        handler.handle(cmd_b),
    )

    statuses = {result_a.status, result_b.status}
    assert statuses == {"RESERVED", "INSUFFICIENT_FUNDS"}

    # в БД ровно одна бронь
    async with maker() as s:
        count = await s.scalar(select(func.count()).select_from(BudgetReservationModel))
        assert count == 1

async def test_reserve_idempotency_returns_same_reservation(engine):
    club_id = uuid.uuid4()
    month = date(2026, 9, 1)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as s:
        await s.execute(
            insert(RewardBudgetModel).values(
                id=uuid.uuid4(), club_id=club_id, budget_month=month,
                revenue_base=Decimal("1000000.00"), configured_limit=Decimal("100000.00"),
                reserved=Decimal("0"), spent=Decimal("0"), released=Decimal("0"), version=0,
            )
        )
        await s.commit()

    handler = ReserveBudgetCommandHandler(uow_factory=lambda: SQLAlchemyUnitOfWork(maker))
    key = f"referral:{uuid.uuid4()}"
    cmd = ReserveBudgetCommand(
        club_id=club_id, source_type="REFERRAL", source_id=uuid.uuid4(),
        amount=Decimal("10000.00"), idempotency_key=key,
    )

    first = await handler.handle(cmd)
    second = await handler.handle(cmd)   # тот же ключ

    assert first.status == "RESERVED"
    assert second.status == "RESERVED"
    assert first.reservation_id == second.reservation_id   # ТОТ ЖЕ id

    async with maker() as s:
        count = await s.scalar(select(func.count()).select_from(BudgetReservationModel))
        assert count == 1

async def test_consume_duplicate_source_key_already_granted(engine):
    club_id = uuid.uuid4()
    month = date(2026, 9, 1)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    budget_id = uuid.uuid4()
    reservation_id = uuid.uuid4()

    async with maker() as s:
        await s.execute(insert(RewardBudgetModel).values(
            id=budget_id, club_id=club_id, budget_month=month,
            revenue_base=Decimal("1000000.00"), configured_limit=Decimal("100000.00"),
            reserved=Decimal("20000.00"), spent=Decimal("0"), released=Decimal("0"), version=0,
        ))
        await s.execute(insert(BudgetReservationModel).values(
            id=reservation_id, budget_id=budget_id, source_type="REFERRAL",
            source_id=uuid.uuid4(), reserved_amount=Decimal("20000.00"),
            consumed_amount=Decimal("0"), idempotency_key=f"k:{uuid.uuid4()}",
            status="ACTIVE", created_at=datetime.now(UTC),
        ))
        await s.commit()

    handler = ConsumeReservationCommandHandler(uow_factory=lambda: SQLAlchemyUnitOfWork(maker))
    key = f"referral_invitee:{uuid.uuid4()}"
    cmd = ConsumeReservationCommand(  # noqa: F821
        reservation_id=reservation_id, amount=Decimal("10000.00"),
        grant_purpose="REFERRAL_INVITEE", client_id=uuid.uuid4(),
        source_key=key, applicable_purchase_type="MEMBERSHIP",
    )

    first = await handler.handle(cmd)
    second = await handler.handle(cmd)   # тот же source_key

    assert first.status == "GRANTED"
    assert second.status == "ALREADY_GRANTED"
    assert first.grant_id == second.grant_id

    async with maker() as s:
        count = await s.scalar(select(func.count()).select_from(DiscountGrantModel))
        assert count == 1


async def test_consume_moves_reserved_to_spent(engine):
    club_id = uuid.uuid4()
    month = date(2026, 9, 1)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    budget_id = uuid.uuid4()
    reservation_id = uuid.uuid4()

    async with maker() as s:
        await s.execute(insert(RewardBudgetModel).values(
            id=budget_id, club_id=club_id, budget_month=month,
            revenue_base=Decimal("1000000.00"), configured_limit=Decimal("100000.00"),
            reserved=Decimal("20000.00"), spent=Decimal("0"), released=Decimal("0"), version=0,
        ))
        await s.execute(insert(BudgetReservationModel).values(
            id=reservation_id, budget_id=budget_id, source_type="REFERRAL",
            source_id=uuid.uuid4(), reserved_amount=Decimal("20000.00"),
            consumed_amount=Decimal("0"), idempotency_key=f"k:{uuid.uuid4()}",
            status="ACTIVE", created_at=datetime.now(UTC),
        ))
        await s.commit()

    handler = ConsumeReservationCommandHandler(uow_factory=lambda: SQLAlchemyUnitOfWork(maker))
    cmd = ConsumeReservationCommand(
        reservation_id=reservation_id, amount=Decimal("15000.00"),
        grant_purpose="REFERRAL_INVITEE", client_id=uuid.uuid4(),
        source_key=f"k:{uuid.uuid4()}", applicable_purchase_type="MEMBERSHIP",
    )

    result = await handler.handle(cmd)
    assert result.status == "GRANTED"

    async with maker() as s:
        budget = await s.get(RewardBudgetModel, budget_id)
        assert budget.reserved == Decimal("5000.00")   # было 20000, ушло 15000
        assert budget.spent == Decimal("15000.00")      # выросло на те же 15000
        reservation = await s.get(BudgetReservationModel, reservation_id)
        assert reservation.consumed_amount == Decimal("15000.00")