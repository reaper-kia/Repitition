class ClientNotFoundError(Exception):
    """Сущность Client не найдена."""


class ClientAlreadyExistsError(Exception):
    """Нарушение уникальности при создании Client."""
