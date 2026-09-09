class RewardsDomainError(Exception):
    """Базовая ошибка домена Rewards."""


class InsufficientBudgetError(RewardsDomainError):
    """В бюджете недостаточно доступных средств."""


class ReservationExhaustedError(RewardsDomainError):
    """Запрошенная сумма превышает остаток резерва."""


class ReservationNotActiveError(RewardsDomainError):
    """Операция недоступна для неактивного резерва."""


class GrantAlreadyRedeemedError(RewardsDomainError):
    """Грант уже был погашен."""


class GrantNotApplicableError(RewardsDomainError):
    """Грант неприменим к указанной покупке."""


class InvalidRewardAmountError(RewardsDomainError):
    """Сумма операции должна быть строго положительной."""
