from dataclasses import dataclass
from decimal import Decimal

from src.shared.domain.exceptions import InvalidCurrencyError, NegativeAmountError


ALLOWED_CURRENCIES = {"USD", "EUR", "RUB"}


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        normalized_currency = self.currency.strip().upper()
        if normalized_currency not in ALLOWED_CURRENCIES:
            raise InvalidCurrencyError(f"Invalid currency: {self.currency}")
        if self.amount < 0:
            raise NegativeAmountError(f"Amount cannot be negative: {self.amount}")
        object.__setattr__(self, "currency", normalized_currency)
