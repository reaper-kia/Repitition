class ClubNotFoundError(Exception):
    """Сущность Club не найдена."""


class ClubAlreadyExistsError(Exception):
    """Нарушение уникальности при создании Club."""
