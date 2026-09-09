class ClientDomainError(Exception):
    """Базовое исключение для доменных ошибок модуля Client."""

    pass


class ClientNotFoundError(ClientDomainError):
    """Сущность Client не найдена."""


class ClientAlreadyExistsError(ClientDomainError):
    """Пользователь уже зарегистрирован как клиент (user_id UNIQUE)."""

    pass


class ClubInactiveError(ClientDomainError):
    """Клуб неактивен, регистрация невозможна."""

    pass


class InvalidReferralCodeError(ClientDomainError):
    """Передан несуществующий или невалидный реферальный код."""

    pass


class SelfReferralError(ClientDomainError):
    """Клиент не может использовать свой собственный реферальный код."""

    pass


class ReferrerAlreadySetError(ClientDomainError):
    """У клиента уже есть реферер, повторная привязка невозможна."""

    pass


class InvalidPurchaseAmountError(ClientDomainError):
    """Некорректная сумма покупки (отрицательная или скидка больше суммы)."""

    pass


class ReferralCodeGenerationError(ClientDomainError):
    pass


class AccessDeniedError(ClientDomainError):
    pass
