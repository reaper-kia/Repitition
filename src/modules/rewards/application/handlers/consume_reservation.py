from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from src.modules.client.domain.enums import PurchaseType
from src.modules.rewards.application.commands.consume_reservation import (
    ConsumeReservationCommand,
    DiscountGrantResult,
)
from src.modules.rewards.domain.entities import DiscountGrant
from src.modules.rewards.domain.enums import GrantPurpose
from src.modules.rewards.domain.exceptions import (
    ReservationExhaustedError,
    ReservationNotActiveError,
)
from src.shared.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


async def consume_reservation_core(
    uow: UnitOfWork, cmd: ConsumeReservationCommand
) -> DiscountGrantResult:
    """Ядро потребления. Открытый uow, flush, без commit."""
    existing = await uow.rewards.get_grant_by_source_key(cmd.source_key)
    if existing is not None:
        return DiscountGrantResult(existing.id, "ALREADY_GRANTED")

    reservation = await uow.rewards.get_reservation_for_update(cmd.reservation_id)
    if reservation is None:
        return DiscountGrantResult(None, "RESERVATION_EXHAUSTED")

    budget = await uow.rewards.get_budget_by_id_for_update(reservation.budget_id)
    if budget is None:
        raise RuntimeError(
            f"Reservation {reservation.id} points to missing budget "
            f"{reservation.budget_id}"
        )

    existing = await uow.rewards.get_grant_by_source_key(cmd.source_key)
    if existing is not None:
        return DiscountGrantResult(existing.id, "ALREADY_GRANTED")

    try:
        reservation.consume(cmd.amount)
        budget.consume(cmd.amount)
    except (ReservationExhaustedError, ReservationNotActiveError):
        return DiscountGrantResult(None, "RESERVATION_EXHAUSTED")

    purpose = GrantPurpose(cmd.grant_purpose)
    grant = DiscountGrant(
        client_id=cmd.client_id,
        reservation_id=reservation.id,
        amount=cmd.amount,
        purpose=purpose,
        applicable_purchase_type=PurchaseType(cmd.applicable_purchase_type),
        source_key=cmd.source_key,
        valid_until=datetime.now(UTC) + timedelta(days=90),
    )
    await uow.rewards.add_grant(grant)
    await uow.rewards.save_reservation(reservation)
    await uow.rewards.save_budget(budget)
    await uow.flush()
    return DiscountGrantResult(grant.id, "GRANTED")


@dataclass
class ConsumeReservationCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: ConsumeReservationCommand) -> DiscountGrantResult:
        async with self.uow_factory() as uow:
            try:
                result = await consume_reservation_core(uow, cmd)
                await uow.commit()
                return result
            except IntegrityError:
                await uow.rollback()
                existing = await uow.rewards.get_grant_by_source_key(cmd.source_key)
                if existing is not None:
                    return DiscountGrantResult(existing.id, "ALREADY_GRANTED")
                raise
