import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from src.modules.rewards.infra.models import RewardBudgetModel, BudgetReservationModel


pytestmark = pytest.mark.integration


async def _make_budget(
    session, *, revenue_base, configured_limit, reserved="0", spent="0"
):
    budget_id = uuid.uuid4()
    await session.execute(
        insert(RewardBudgetModel).values(
            id=budget_id,
            club_id=uuid.uuid4(),
            budget_month=date(2026, 9, 1),
            revenue_base=Decimal(revenue_base),
            configured_limit=Decimal(configured_limit),
            reserved=Decimal(reserved),
            spent=Decimal(spent),
            released=Decimal("0"),
            version=0,
        )
    )
    return budget_id


async def test_budget_limit_constraint_blocks_over_4_percent(session):
    # выручка 1 000 000 -> 4% = 40 000. Лимит клуба выше, значит потолок = 40 000.
    # Пытаемся зарезервировать 50 000 сырым INSERT, мимо домена.
    with pytest.raises(IntegrityError):
        await _make_budget(
            session,
            revenue_base="1000000.00",
            configured_limit="100000.00",
            reserved="50000.00",
        )
        await session.flush()


async def test_budget_non_negative_constraint(session):
    with pytest.raises(IntegrityError):
        await _make_budget(
            session,
            revenue_base="1000000.00",
            configured_limit="100000.00",
            reserved="-10.00",
        )
        await session.flush()


async def test_reservation_consumed_not_over_reserved(session):
    budget_id = await _make_budget(
        session, revenue_base="1000000.00", configured_limit="100000.00"
    )
    await session.flush()
    with pytest.raises(IntegrityError):
        await session.execute(
            insert(BudgetReservationModel).values(
                id=uuid.uuid4(),
                budget_id=budget_id,
                source_type="REFERRAL",
                source_id=uuid.uuid4(),
                reserved_amount=Decimal("100.00"),
                consumed_amount=Decimal("150.00"),  # больше зарезервированного
                idempotency_key=f"test:{uuid.uuid4()}",
                status="ACTIVE",
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.flush()
