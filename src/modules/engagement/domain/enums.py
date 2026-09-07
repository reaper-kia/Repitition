from enum import StrEnum


class ChallengeStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ClientChallengeStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class AchievementRuleType(StrEnum):
    VISITS_TOTAL = "VISITS_TOTAL"
    CHALLENGE_STAGE = "CHALLENGE_STAGE"
    LEADERBOARD_TOP = "LEADERBOARD_TOP"


class RetentionCaseStatus(StrEnum):
    OPEN = "OPEN"
    OFFER_CREATED = "OFFER_CREATED"
    DISMISSED = "DISMISSED"


class RetentionDecision(StrEnum):
    DISMISS = "DISMISS"
    OFFER_DISCOUNT = "OFFER_DISCOUNT"