from dataclasses import dataclass
from uuid import UUID

from src.modules.client.domain.enums import MembershipType


@dataclass(frozen=True)
class CreateClientCommand:
    user_id: UUID
    club_id: UUID
    display_name: str
    membership_type: MembershipType
    referral_code: str | None = None