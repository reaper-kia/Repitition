from dataclasses import dataclass

from src.modules.club.domain.exceptions import (
    InvalidCityError,
    InvalidClubNameError,
)


@dataclass(frozen=True)
class ClubName:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()

        if not normalized:
            raise InvalidClubNameError("Club name cannot be empty")

        if len(normalized) > 255:
            raise InvalidClubNameError("Club name must not exceed 255 characters")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class City:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()

        if not normalized:
            raise InvalidCityError("City cannot be empty")

        if len(normalized) > 120:
            raise InvalidCityError("City must not exceed 120 characters")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
