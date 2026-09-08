from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from src.modules.rewards.application.commands.consume_reservation import (
    ConsumeReservationCommand,
    DiscountGrantResult,
)
from src.modules.client.domain.enums import PurchaseType
from src.modules.rewards.domain.entities import DiscountGrant
from src.modules.rewards.domain.enums import GrantPurpose
from src.modules.rewards.domain.exceptions import ReservationExhaustedError
from src.shared.application.unit_of_work import UnitOfWorkFactory


@dataclass
class ConsumeReservationCommandHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: ConsumeReservationCommand) -> DiscountGrantResult:
        async with self.uow_factory() as uow:
            # ранняя проверка source_key: грант уже выдавали -> ALREADY_GRANTED
            existing = await uow.rewards.get_grant_by_source_key(cmd.source_key)
            if existing is not None:
                return DiscountGrantResult(grant_id=existing.id, status="ALREADY_GRANTED")

            reservation = await uow.rewards.get_reservation_for_update(cmd.reservation_id)
            if reservation is None:
                return DiscountGrantResult(grant_id=None, status="RESERVATION_EXHAUSTED")

            budget = await uow.rewards.get_budget_by_id_for_update(
                reservation.budget_id
            )

            # двойная бухгалтерия: резервация И бюджет
            try:
                reservation.consume(cmd.amount)
                budget.consume(cmd.amount)
            except ReservationExhaustedError:
                return DiscountGrantResult(grant_id=None, status="RESERVATION_EXHAUSTED")

            grant = DiscountGrant(
                client_id=cmd.client_id,
                reservation_id=reservation.id,
                amount=cmd.amount,
                purpose=GrantPurpose(cmd.grant_purpose),
                applicable_purchase_type=PurchaseType(cmd.applicable_purchase_type),
                source_key=cmd.source_key,
                valid_until=datetime.now(UTC) + timedelta(days=90),
            )
            await uow.rewards.add_grant(grant)
            await uow.rewards.save_reservation(reservation)
            await uow.rewards.save_budget(budget)

            # flush ВНУТРИ try — ловим гонку по source_key здесь, а не на commit
            try:
                await uow.session.flush()
            except IntegrityError:
                await uow.rollback()
                existing = await uow.rewards.get_grant_by_source_key(cmd.source_key)
                return DiscountGrantResult(
                    grant_id=existing.id if existing else None,
                    status="ALREADY_GRANTED",
                )

            await uow.commit()
            return DiscountGrantResult(grant_id=grant.id, status="GRANTED")