class ClubDomainError(Exception):
    pass


class ClubNotFoundError(ClubDomainError):
    pass


class ClubAlreadyExistsError(ClubDomainError):
    pass


class InvalidClubNameError(ClubDomainError):
    pass


class InvalidCityError(ClubDomainError):
    pass


class ManagerUserNotFoundError(ClubDomainError):
    pass


class ManagerUserNotClubManagerError(ClubDomainError):
    pass