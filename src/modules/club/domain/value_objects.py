from dataclasses import dataclass

from src.modules.club.domain.exceptions import InvalidClubNameError, InvalidCityError


@dataclass(frozen=True)
class ClubName:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidClubNameError("Club name cannot be empty")
        if len(normalized) > 255:
            raise InvalidClubNameError("Club name too long (max 255)")
        # сохраняем нормализованное значение
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class City:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidCityError("City cannot be empty")
        if len(normalized) > 120:
            raise InvalidCityError("City too long (max 120)")
        object.__setattr__(self, "value", normalized)