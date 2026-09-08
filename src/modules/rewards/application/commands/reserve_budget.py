from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class ReserveBudgetCommand:
    club_id: UUID
    source_type: Literal["REFERRAL", "RETENTION"]
    source_id: UUID
    amount: Decimal
    idempotency_key: str


@dataclass(frozen=True)
class BudgetReservationResult:
    reservation_id: UUID | None
    status: Literal["RESERVED", "INSUFFICIENT_FUNDS"]
