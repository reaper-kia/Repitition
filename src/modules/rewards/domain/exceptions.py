class RewardsNotFoundError(Exception):
    """Сущность Rewards не найдена."""


class RewardsAlreadyExistsError(Exception):
    """Нарушение уникальности при создании Rewards."""
