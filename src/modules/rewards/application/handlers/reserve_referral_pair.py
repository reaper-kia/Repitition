from dataclasses import dataclass
from datetime import date

from src.modules.rewards.application.commands.reserve_referral_pair import (
    ReferralPairResult,
    ReserveReferralPairCommand,
)
from src.modules.rewards.domain.entities import BudgetReservation
from src.modules.rewards.domain.enums import ReservationSourceType
from src.modules.rewards.domain.exceptions import InsufficientBudgetError
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class ReserveReferralPairCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: ReserveReferralPairCommand) -> ReferralPairResult:
        budget_month = date.today().replace(day=1)

        async with self.uow_factory() as uow:
            # идемпотентность по паре: одна из двух броней уже есть -> вся пара уже создана
            existing = await uow.rewards.get_reservation_by_idempotency_key(
                f"{cmd.idempotency_key}:invitee"
            )
            if existing is not None:
                referrer = await uow.rewards.get_reservation_by_idempotency_key(
                    f"{cmd.idempotency_key}:referrer"
                )
                return ReferralPairResult(
                    invitee_reservation_id=existing.id,
                    referrer_reservation_id=referrer.id if referrer else None,
                    status="RESERVED",
                )

            # КЛЮЧЕВОЕ: лочим бюджеты СТРОГО в порядке возрастания club_id
            sides = sorted(
                [
                    ("invitee", cmd.invitee_club_id, cmd.invitee_amount),
                    ("referrer", cmd.referrer_club_id, cmd.referrer_amount),
                ],
                key=lambda s: s[1],  # по club_id
            )

            budgets = {}
            for role, club_id, amount in sides:
                budget = await uow.rewards.get_budget_for_update(club_id, budget_month)
                if budget is None:
                    return ReferralPairResult(None, None, "INSUFFICIENT_FUNDS")
                try:
                    budget.reserve(amount)
                except InsufficientBudgetError:
                    return ReferralPairResult(None, None, "INSUFFICIENT_FUNDS")
                budgets[role] = budget

            # обе проверки прошли — создаём обе брони
            reservations = {}
            for role, _, amount in sides:
                r = BudgetReservation(
                    budget_id=budgets[role].id,
                    source_type=ReservationSourceType.REFERRAL,
                    source_id=cmd.source_id,
                    reserved_amount=amount,
                    idempotency_key=f"{cmd.idempotency_key}:{role}",
                )
                await uow.rewards.add_reservation(r)
                await uow.rewards.save_budget(budgets[role])
                reservations[role] = r

            await uow.commit()
            return ReferralPairResult(
                invitee_reservation_id=reservations["invitee"].id,
                referrer_reservation_id=reservations["referrer"].id,
                status="RESERVED",
            )