from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.modules.visit.domain.exceptions import InvalidVisitPeriodError


@dataclass
class Visit:
    """Физический проход через турникет. Владелец — Visit Module.

    Создаётся ТОЛЬКО импортом/адаптером турникета. Ни клиент, ни управляющий
    не могут создать или отредактировать подтверждённый проход — иначе
    вся геймификация становится фармабельной.

    external_id — идентификатор из системы турникетов, UNIQUE. Он и есть
    защита от повторной загрузки: Engagement на своей стороне идемпотентность
    не дублирует, это ответственность Visit.
    """

    external_id: str
    client_id: UUID
    club_id: UUID
    entered_at: datetime
    exited_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def record(
        cls,
        external_id: str,
        client_id: UUID,
        club_id: UUID,
        entered_at: datetime,
        exited_at: datetime | None = None,
    ) -> "Visit":
        if exited_at is not None and exited_at < entered_at:
            raise InvalidVisitPeriodError("exited_at must not be earlier than entered_at")
        return cls(
            external_id=external_id,
            client_id=client_id,
            club_id=club_id,
            entered_at=entered_at,
            exited_at=exited_at,
        )

    def close(self, exited_at: datetime) -> None:
        if exited_at < self.entered_at:
            raise InvalidVisitPeriodError("exited_at must not be earlier than entered_at")
        self.exited_at = exited_at