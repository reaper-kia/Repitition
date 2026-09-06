class UserDomainError(Exception):
    """Base Exception"""


class InvalidEmailError(UserDomainError):
    pass


class InvalidUserNameError(UserDomainError):
    pass


class EmailAlreadyExistError(UserDomainError):
    pass


class WeakPasswordError(UserDomainError):
    pass


class UserNotFoundError(UserDomainError):
    pass


class PublicAdminRegistrationForbiddenError(UserDomainError):
    pass
