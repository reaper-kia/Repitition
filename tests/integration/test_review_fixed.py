import asyncio
import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.modules.rewards.application.commands.reserve_budget import ReserveBudgetCommand
from src.modules.rewards.application.commands.reserve_referral_pair import (
    ReserveReferralPairCommand,
)
from src.modules.rewards.application.handlers.reserve_budget import (
    ReserveBudgetCommandHandler,
    reserve_budget_core,
)
from src.modules.rewards.application.handlers.reserve_referral_pair import (
    ReserveReferralPairCommandHandler,
)
from src.modules.rewards.domain.entities import RewardBudget
from src.modules.rewards.domain.exceptions import InvalidRewardAmountError
from src.modules.rewards.infra.models import (
    BudgetReservationModel,
    RewardBudgetModel,
)
from src.shared.infra.database.unit_of_work import SQLAlchemyUnitOfWork

pytestmark = pytest.mark.integration


async def _insert_budget(
    maker, club_id, *, reserved="0", spent="0", revenue="1000000.00", limit="100000.00"
):
    async with maker() as s:
        await s.execute(
            insert(RewardBudgetModel).values(
                id=uuid.uuid4(),
                club_id=club_id,
                budget_month=date(2026, 9, 1),
                revenue_base=Decimal(revenue),
                configured_limit=Decimal(limit),
                reserved=Decimal(reserved),
                spent=Decimal(spent),
                released=Decimal("0"),
                version=0,
            )
        )
        await s.commit()


# ---------- пункт 3: неположительные суммы ----------


def test_domain_reserve_zero_raises_and_keeps_state():
    b = RewardBudget(
        club_id=uuid.uuid4(),
        budget_month=date(2026, 9, 1),
        revenue_base=Decimal("1000000"),
        configured_limit=Decimal("100000"),
        reserved=Decimal("100"),
        spent=Decimal("0"),
    )
    with pytest.raises(InvalidRewardAmountError):
        b.reserve(Decimal("0"))
    assert b.reserved == Decimal("100")  # состояние не тронуто


def test_domain_consume_negative_raises_and_keeps_state():
    b = RewardBudget(
        club_id=uuid.uuid4(),
        budget_month=date(2026, 9, 1),
        revenue_base=Decimal("1000000"),
        configured_limit=Decimal("100000"),
        reserved=Decimal("100"),
        spent=Decimal("0"),
    )
    with pytest.raises(InvalidRewardAmountError):
        b.consume(Decimal("-10"))
    assert b.reserved == Decimal("100")
    assert b.spent == Decimal("0")  # НЕ ушёл в минус


# ---------- пункт 4: пара из одного клуба ----------


async def test_pair_same_club_sum_exceeds_budget(engine):
    club = uuid.uuid4()
    maker = async_sessionmaker(engine, expire_on_commit=False)
    # лимит 40 000 (1млн * 4%); каждая доля по 30k влезает, сумма 60k — нет
    await _insert_budget(maker, club, revenue="1000000.00")

    handler = ReserveReferralPairCommandHandler(
        uow_factory=lambda: SQLAlchemyUnitOfWork(maker)
    )
    cmd = ReserveReferralPairCommand(
        invitee_club_id=club,
        invitee_amount=Decimal("30000.00"),
        referrer_club_id=club,
        referrer_amount=Decimal("30000.00"),
        source_id=uuid.uuid4(),
        idempotency_key=f"pair:{uuid.uuid4()}",
    )
    result = await handler.handle(cmd)

    assert result.status == "INSUFFICIENT_FUNDS"
    async with maker() as s:
        count = await s.scalar(select(func.count()).select_from(BudgetReservationModel))
        assert count == 0  # ни одной брони


async def test_pair_same_club_fits_debits_full_sum(engine):
    club = uuid.uuid4()
    maker = async_sessionmaker(engine, expire_on_commit=False)
    await _insert_budget(maker, club, revenue="1000000.00")  # лимит 40k

    handler = ReserveReferralPairCommandHandler(
        uow_factory=lambda: SQLAlchemyUnitOfWork(maker)
    )
    cmd = ReserveReferralPairCommand(
        invitee_club_id=club,
        invitee_amount=Decimal("15000.00"),
        referrer_club_id=club,
        referrer_amount=Decimal("10000.00"),
        source_id=uuid.uuid4(),
        idempotency_key=f"pair:{uuid.uuid4()}",
    )
    result = await handler.handle(cmd)

    assert result.status == "RESERVED"
    async with maker() as s:
        count = await s.scalar(select(func.count()).select_from(BudgetReservationModel))
        assert count == 2  # две брони
        budget = await s.scalar(select(RewardBudgetModel))
        assert budget.reserved == Decimal("25000.00")  # 15k+10k, не перезатёрто


# ---------- пункт 5: параллельный одинаковый ключ ----------


async def test_parallel_same_idempotency_key(engine):
    club = uuid.uuid4()
    maker = async_sessionmaker(engine, expire_on_commit=False)
    await _insert_budget(maker, club, revenue="1000000.00")

    handler = ReserveBudgetCommandHandler(
        uow_factory=lambda: SQLAlchemyUnitOfWork(maker)
    )
    key = f"referral:{uuid.uuid4()}"
    cmd = ReserveBudgetCommand(
        club_id=club,
        source_type="REFERRAL",
        source_id=uuid.uuid4(),
        amount=Decimal("10000.00"),
        idempotency_key=key,
    )

    r1, r2 = await asyncio.gather(handler.handle(cmd), handler.handle(cmd))

    assert r1.status == "RESERVED"
    assert r2.status == "RESERVED"
    assert r1.reservation_id == r2.reservation_id  # один id
    async with maker() as s:
        count = await s.scalar(select(func.count()).select_from(BudgetReservationModel))
        assert count == 1  # одна строка
        budget = await s.scalar(select(RewardBudgetModel))
        assert budget.reserved == Decimal("10000.00")  # списано один раз


# ---------- пункт 7: общая транзакция, откат при падении соседа ----------


async def test_shared_transaction_rolls_back_on_caller_failure(engine):
    club = uuid.uuid4()
    maker = async_sessionmaker(engine, expire_on_commit=False)
    await _insert_budget(maker, club, revenue="1000000.00")

    cmd = ReserveBudgetCommand(
        club_id=club,
        source_type="REFERRAL",
        source_id=uuid.uuid4(),
        amount=Decimal("10000.00"),
        idempotency_key=f"referral:{uuid.uuid4()}",
    )

    # имитируем вызов из Client: ядро в общей транзакции, потом Client падает
    uow = SQLAlchemyUnitOfWork(maker)
    with pytest.raises(RuntimeError):
        async with uow:
            result = await reserve_budget_core(uow, cmd)
            assert result.status == "RESERVED"  # ядро отработало
            raise RuntimeError("Client save failed")  # сосед упал
            # commit НЕ достигается

    # проверяем: резерв откатился вместе с "клиентом"
    async with maker() as s:
        count = await s.scalar(select(func.count()).select_from(BudgetReservationModel))
        assert count == 0  # ничего не сохранилось
        budget = await s.scalar(select(RewardBudgetModel))
        assert budget.reserved == Decimal("0")  # бюджет не тронут
