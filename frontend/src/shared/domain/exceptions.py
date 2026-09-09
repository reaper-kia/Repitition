class SharedDomainError(Exception):
    pass


class InvalidCurrencyError(SharedDomainError):
    """Неподдерживаемая валюта (только USD, EUR)."""

    pass


class NegativeAmountError(SharedDomainError):
    """Отрицательная сумма денег."""

    pass
