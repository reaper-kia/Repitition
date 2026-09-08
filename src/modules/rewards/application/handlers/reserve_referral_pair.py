from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from src.modules.rewards.application.commands.reserve_referral_pair import (
    ReferralPairResult,
    ReserveReferralPairCommand,
)
from src.modules.rewards.domain.entities import BudgetReservation
from src.modules.rewards.domain.enums import ReservationSourceType
from src.modules.rewards.domain.exceptions import (
    InsufficientBudgetError,
    InvalidRewardAmountError,
)
from src.shared.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


async def reserve_referral_pair_core(
    uow: UnitOfWork, cmd: ReserveReferralPairCommand
) -> ReferralPairResult:
    """Ядро резерва пары. Открытый uow, flush, без commit.
    Группирует суммы по club_id — корректно, если оба клиента в одном клубе."""
    budget_month = date.today().replace(day=1)
    invitee_key = f"{cmd.idempotency_key}:invitee"
    referrer_key = f"{cmd.idempotency_key}:referrer"

    existing = await uow.rewards.get_reservation_by_idempotency_key(invitee_key)
    if existing is not None:
        referrer = await uow.rewards.get_reservation_by_idempotency_key(referrer_key)
        return ReferralPairResult(
            existing.id, referrer.id if referrer else None, "RESERVED"
        )

    # суммы по клубу: один клуб -> суммы складываются в один reserve()
    amount_by_club: dict = {}
    amount_by_club[cmd.invitee_club_id] = (
        amount_by_club.get(cmd.invitee_club_id, Decimal("0")) + cmd.invitee_amount
    )
    amount_by_club[cmd.referrer_club_id] = (
        amount_by_club.get(cmd.referrer_club_id, Decimal("0")) + cmd.referrer_amount
    )

    budgets: dict = {}
    for club_id in sorted(amount_by_club.keys()):
        budget = await uow.rewards.get_budget_for_update(club_id, budget_month)
        if budget is None:
            return ReferralPairResult(None, None, "INSUFFICIENT_FUNDS")
        try:
            budget.reserve(amount_by_club[club_id])
        except InsufficientBudgetError:
            return ReferralPairResult(None, None, "INSUFFICIENT_FUNDS")
        except InvalidRewardAmountError:
            raise
        budgets[club_id] = budget

    existing = await uow.rewards.get_reservation_by_idempotency_key(invitee_key)
    if existing is not None:
        referrer = await uow.rewards.get_reservation_by_idempotency_key(referrer_key)
        return ReferralPairResult(
            existing.id, referrer.id if referrer else None, "RESERVED"
        )

    invitee_res = BudgetReservation(
        budget_id=budgets[cmd.invitee_club_id].id,
        source_type=ReservationSourceType.REFERRAL,
        source_id=cmd.source_id,
        reserved_amount=cmd.invitee_amount,
        idempotency_key=invitee_key,
    )
    referrer_res = BudgetReservation(
        budget_id=budgets[cmd.referrer_club_id].id,
        source_type=ReservationSourceType.REFERRAL,
        source_id=cmd.source_id,
        reserved_amount=cmd.referrer_amount,
        idempotency_key=referrer_key,
    )
    await uow.rewards.add_reservation(invitee_res)
    await uow.rewards.add_reservation(referrer_res)
    for budget in budgets.values():
        await uow.rewards.save_budget(budget)
    await uow.flush()
    return ReferralPairResult(invitee_res.id, referrer_res.id, "RESERVED")


@dataclass
class ReserveReferralPairCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: ReserveReferralPairCommand) -> ReferralPairResult:
        invitee_key = f"{cmd.idempotency_key}:invitee"
        referrer_key = f"{cmd.idempotency_key}:referrer"
        async with self.uow_factory() as uow:
            try:
                result = await reserve_referral_pair_core(uow, cmd)
                await uow.commit()
                return result
            except IntegrityError:
                await uow.rollback()
                inv = await uow.rewards.get_reservation_by_idempotency_key(invitee_key)
                ref = await uow.rewards.get_reservation_by_idempotency_key(referrer_key)
                if inv is not None and ref is not None:
                    return ReferralPairResult(inv.id, ref.id, "RESERVED")
                raise
