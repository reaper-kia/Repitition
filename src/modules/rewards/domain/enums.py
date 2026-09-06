from enum import StrEnum


class ReservationSourceType(StrEnum):
    """Откуда пришёл запрос на резерв.

    CHALLENGE_COHORT здесь БОЛЬШЕ НЕТ: онбординг стал неденежным,
    и резервировать под месячный набор больше не нужно. Осталось два
    адресных сценария — это ровно то, чего требует ограничение кейса
    "скидка не должна доставаться тем, кто и так лоялен".
    """

    REFERRAL = "REFERRAL"
    RETENTION = "RETENTION"


class ReservationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CONSUMED = "CONSUMED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class GrantPurpose(StrEnum):
    REFERRAL_INVITEE = "REFERRAL_INVITEE"
    REFERRAL_REFERRER = "REFERRAL_REFERRER"
    RETENTION = "RETENTION"


class GrantStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    REDEEMED = "REDEEMED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"