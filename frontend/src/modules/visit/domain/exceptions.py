class VisitNotFoundError(Exception):
    """Сущность Visit не найдена."""


class VisitAlreadyExistsError(Exception):
    """Нарушение уникальности при создании Visit."""
