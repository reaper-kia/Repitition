class VisitDomainError(Exception):
    """Базовое исключение для доменных ошибок модуля Visit."""
    pass

class InvalidVisitPeriodError(VisitDomainError):
    """Время выхода раньше времени входа (защита от невалидных данных турникета)."""
    pass

class VisitAlreadyClosedError(VisitDomainError):
    """Попытка закрыть визит, который уже закрыт (двойной проход на выход)."""
    pass

class VisitNotFoundError(VisitDomainError):
    """Визит не найден (например, по external_id или id)."""
    pass

class ExternalIdAlreadyExistsError(VisitDomainError):
    """Нарушение идемпотентности: турникет прислал дубликат external_id."""
    pass

class ClientSnapshotNotFoundError(VisitDomainError):
    """Клиент не найден в снапшоте (не существует или не привязан к клубу)."""
    pass