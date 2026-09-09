from enum import StrEnum

class VisitStatus(StrEnum):
    """Статус физического присутствия клиента в клубе."""
    OPEN = "OPEN"       # Клиент внутри (турникет сработал на вход)
    CLOSED = "CLOSED"   # Клиент вышел (турникет сработал на выход)