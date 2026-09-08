import calendar
import random
import re
from dataclasses import dataclass
from datetime import datetime, UTC

from src.modules.client.domain.enums import MembershipType

@dataclass(frozen=True)
class Membership:
    """Value Object, представляющий абонемент клиента."""
    type: MembershipType
    expires_at: datetime

    def is_active(self, at: datetime | None = None) -> bool:
        """Проверяет, действителен ли абонемент на указанный момент времени."""
        check_time = at or datetime.now(UTC)
        return self.expires_at > check_time

    def extended_by(self, months: int) -> "Membership":
        if months <= 0:
            raise ValueError("Months to extend must be positive")
            
        total_months = self.expires_at.month + months - 1
        year = self.expires_at.year + total_months // 12
        month = total_months % 12 + 1
        day = min(self.expires_at.day, calendar.monthrange(year, month)[1])
        
        new_expires_at = self.expires_at.replace(year=year, month=month, day=day)
        return Membership(type=self.type, expires_at=new_expires_at)


@dataclass(frozen=True)
class ReferralCode:
    """Value Object для реферального кода.
    6 символов, верхний регистр, A-Z0-9 без визуально похожих (0, O, 1, I, L).
    """
    value: str

    # Разрешенные символы: A-H, J-K, M-N, P-Z, 2-9
    _PATTERN = re.compile(r"^[A-HJ-KM-NP-Z2-9]{6}$")

    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(
                "Referral code must be 6 uppercase alphanumeric chars "
                "excluding 0, O, 1, I, L"
            )

    @classmethod
    def generate(cls) -> "ReferralCode":
        """Генерирует случайный валидный код. 
        Проверка на коллизии (UNIQUE) и цикл до 5 попыток должны 
        происходить в Application Handler, а не здесь.
        """
        chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
        code = "".join(random.choices(chars, k=6))
        return cls(value=code)