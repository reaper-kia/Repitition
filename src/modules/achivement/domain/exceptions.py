class AchivementNotFoundError(Exception):
    """Сущность Achivement не найдена."""


class AchivementAlreadyExistsError(Exception):
    """Нарушение уникальности при создании Achivement."""
