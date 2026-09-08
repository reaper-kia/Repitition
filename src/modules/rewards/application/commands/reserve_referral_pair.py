from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class ReserveReferralPairCommand:
    """Резерв обеих сторон реферала разом. Клубы могут быть разными.

    Блокировка обоих бюджетов в порядке возрастания club_id — защита
    от дедлока при зеркальных параллельных регистрациях.
    """
    invitee_club_id: UUID
    invitee_amount: Decimal
    referrer_club_id: UUID
    referrer_amount: Decimal
    source_id: UUID            # client_id новичка — общий для пары
    idempotency_key: str


@dataclass(frozen=True)
class ReferralPairResult:
    invitee_reservation_id: UUID | None
    referrer_reservation_id: UUID | None
    status: Literal["RESERVED", "INSUFFICIENT_FUNDS"]