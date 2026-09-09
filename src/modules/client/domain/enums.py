from enum import StrEnum


class MembershipType(StrEnum):
    ONE_MONTH = "ONE_MONTH"
    THREE_MONTHS = "THREE_MONTHS"
    SIX_MONTHS = "SIX_MONTHS"
    TWELVE_MONTHS = "TWELVE_MONTHS"


class ClientStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"


class AcquisitionChannel(StrEnum):
    ORGANIC = "ORGANIC"
    REFERRAL = "REFERRAL"


class PurchaseType(StrEnum):
    MEMBERSHIP = "MEMBERSHIP"
