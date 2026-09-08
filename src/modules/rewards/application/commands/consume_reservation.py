from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class ConsumeReservationCommand:
    reservation_id: UUID
    amount: Decimal
    grant_purpose: Literal["REFERRAL_INVITEE", "REFERRAL_REFERRER", "RETENTION"]
    client_id: UUID
    source_key: str
    applicable_purchase_type: Literal["MEMBERSHIP", "RENEWAL", "PERSONAL_TRAINING", "PRODUCT"]


@dataclass(frozen=True)
class DiscountGrantResult:
    grant_id: UUID | None
    status: Literal["GRANTED", "ALREADY_GRANTED", "RESERVATION_EXHAUSTED"]