from dataclasses import dataclass
from datetime import date

from sqlalchemy.exc import IntegrityError

from src.modules.rewards.application.commands.reserve_budget import (
    BudgetReservationResult,
    ReserveBudgetCommand,
)
from src.modules.rewards.domain.entities import BudgetReservation
from src.modules.rewards.domain.enums import ReservationSourceType
from src.modules.rewards.domain.exceptions import (
    InsufficientBudgetError,
    InvalidRewardAmountError,
)
from src.shared.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


async def reserve_budget_core(
    uow: UnitOfWork, cmd: ReserveBudgetCommand
) -> BudgetReservationResult:
    """Ядро резерва. Принимает ОТКРЫТЫЙ uow, делает flush, НЕ коммитит."""
    budget_month = date.today().replace(day=1)

    existing = await uow.rewards.get_reservation_by_idempotency_key(cmd.idempotency_key)
    if existing is not None:
        return BudgetReservationResult(existing.id, "RESERVED")

    budget = await uow.rewards.get_budget_for_update(cmd.club_id, budget_month)
    if budget is None:
        return BudgetReservationResult(None, "INSUFFICIENT_FUNDS")

    try:
        budget.reserve(cmd.amount)
    except InsufficientBudgetError:
        return BudgetReservationResult(None, "INSUFFICIENT_FUNDS")
    except InvalidRewardAmountError:
        raise

    existing = await uow.rewards.get_reservation_by_idempotency_key(cmd.idempotency_key)
    if existing is not None:
        return BudgetReservationResult(existing.id, "RESERVED")

    reservation = BudgetReservation(
        budget_id=budget.id,
        source_type=ReservationSourceType(cmd.source_type),
        source_id=cmd.source_id,
        reserved_amount=cmd.amount,
        idempotency_key=cmd.idempotency_key,
    )
    await uow.rewards.add_reservation(reservation)
    await uow.rewards.save_budget(budget)
    await uow.flush()
    return BudgetReservationResult(reservation.id, "RESERVED")


@dataclass
class ReserveBudgetCommandHandler:
    """Standalone-обёртка: открывает транзакцию, коммитит, ловит гонку по ключу."""

    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: ReserveBudgetCommand) -> BudgetReservationResult:
        async with self.uow_factory() as uow:
            try:
                result = await reserve_budget_core(uow, cmd)
                await uow.commit()
                return result
            except IntegrityError:
                await uow.rollback()
                existing = await uow.rewards.get_reservation_by_idempotency_key(
                    cmd.idempotency_key
                )
                if existing is not None:
                    return BudgetReservationResult(existing.id, "RESERVED")
                raise
