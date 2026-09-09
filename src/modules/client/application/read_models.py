from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.modules.client.domain.enums import (
    AcquisitionChannel,
    ClientStatus,
    MembershipType,
)


@dataclass(frozen=True)
class ClientReadModel:
    id: UUID
    user_id: UUID
    club_id: UUID
    display_name: str
    membership_type: MembershipType
    membership_expires_at: datetime
    referral_code: str
    referred_by_client_id: UUID | None
    acquisition_channel: AcquisitionChannel
    status: ClientStatus
    registered_at: datetime


@dataclass(frozen=True)
class ClientPageReadModel:
    items: list[ClientReadModel]
    total: int
