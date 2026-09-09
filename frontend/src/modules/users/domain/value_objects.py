from dataclasses import dataclass

from src.modules.users.domain.exceptions import (
    InvalidEmailError,
    InvalidUserNameError,
    WeakPasswordError,
)


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        normalized = self.value.strip().lower()

        if not normalized:
            raise InvalidEmailError("Email cann`t be empty")

        if "@" not in normalized:
            raise InvalidEmailError("Invalid email format")

        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class UserName:
    value: str

    def __post_init__(self):
        normalized = self.value.strip()

        if not normalized:
            raise InvalidUserNameError("Email cann`t be empty")

        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class RawPassword:
    value: str

    def __post_init__(self) -> None:
        if len(self.value) < 8:
            raise WeakPasswordError("Password must contain at least 8 characters")

        if len(self.value) > 128:
            raise WeakPasswordError("Password is too long")
