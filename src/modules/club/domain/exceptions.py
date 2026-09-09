class ClubDomainError(Exception):
    """Базовая ошибка домена Club."""


class ClubNotFoundError(ClubDomainError):
    """Клуб не найден."""


class ClubAlreadyExistsError(ClubDomainError):
    """Клуб с такими уникальными данными уже существует."""


class InvalidClubNameError(ClubDomainError):
    """Название клуба не прошло доменную валидацию."""


class InvalidCityError(ClubDomainError):
    """Название города не прошло доменную валидацию."""


class ManagerUserNotFoundError(ClubDomainError):
    """Пользователь, назначаемый управляющим, не найден."""


class ManagerUserNotClubManagerError(ClubDomainError):
    """Пользователь не имеет роли CLUB_MANAGER."""
