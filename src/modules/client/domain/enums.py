from enum import StrEnum


class ClientStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"


class MembershipType(StrEnum):
    SIX_MONTHS = "SIX_MONTHS"
    TWELVE_MONTHS = "TWELVE_MONTHS"


class PurchaseType(StrEnum):
    MEMBERSHIP = "MEMBERSHIP"
    RENEWAL = "RENEWAL"
    PERSONAL_TRAINING = "PERSONAL_TRAINING"
    PRODUCT = "PRODUCT"


class AcquisitionChannel(StrEnum):
    ORGANIC = "ORGANIC"
    REFERRAL = "REFERRAL"
    ADS = "ADS"
    PARTNER = "PARTNER"
