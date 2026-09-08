from dataclasses import dataclass
from datetime import date

from src.modules.rewards.application.commands.reserve_budget import (
    BudgetReservationResult,
    ReserveBudgetCommand,
)
from src.modules.rewards.domain.entities import BudgetReservation
from src.modules.rewards.domain.enums import ReservationSourceType
from src.modules.rewards.domain.exceptions import InsufficientBudgetError
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class ReserveBudgetCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: ReserveBudgetCommand) -> BudgetReservationResult:
        budget_month = date.today().replace(day=1)

        async with self.uow_factory() as uow:
            # 1. идемпотентность: повтор с тем же ключом -> старая бронь
            existing = await uow.rewards.get_reservation_by_idempotency_key(
                cmd.idempotency_key
            )
            if existing is not None:
                return BudgetReservationResult(
                    reservation_id=existing.id, status="RESERVED"
                )

            # 2. бюджет с блокировкой строки
            budget = await uow.rewards.get_budget_for_update(cmd.club_id, budget_month)
            if budget is None:
                return BudgetReservationResult(
                    reservation_id=None, status="INSUFFICIENT_FUNDS"
                )

            # 3. доменная проверка лимита -> исключение в статус
            try:
                budget.reserve(cmd.amount)
            except InsufficientBudgetError:
                return BudgetReservationResult(
                    reservation_id=None, status="INSUFFICIENT_FUNDS"
                )

            # 4. создаём бронь и сохраняем изменённый бюджет — одна транзакция
            reservation = BudgetReservation(
                budget_id=budget.id,
                source_type=ReservationSourceType(cmd.source_type),
                source_id=cmd.source_id,
                reserved_amount=cmd.amount,
                idempotency_key=cmd.idempotency_key,
            )
            await uow.rewards.add_reservation(reservation)
            await uow.rewards.save_budget(budget)
            await uow.commit()

            return BudgetReservationResult(
                reservation_id=reservation.id, status="RESERVED"
            )