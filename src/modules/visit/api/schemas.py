from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from src.modules.visit.domain.entities import Visit
from src.modules.visit.application.read_models import VisitReadModel


# ==================== REQUEST ====================

class RecordVisitRequest(BaseModel):
    """Запрос от турникета: клиент вошёл."""
    external_id: str = Field(..., description="Уникальный ID прохода из системы турникетов")
    client_id: UUID
    club_id: UUID
    entered_at: datetime


class CloseVisitRequest(BaseModel):
    """Запрос от турникета: клиент вышел."""
    external_id: str = Field(..., description="Тот же ID прохода, что и при входе")
    exited_at: datetime


# ==================== RESPONSE ====================

class VisitResponse(BaseModel):
    """Ответ с данными о визите."""
    id: UUID
    external_id: str
    client_id: UUID
    club_id: UUID
    entered_at: datetime
    exited_at: datetime | None
    
    # Для удобства фронта добавим вычисляемый статус
    status: str = Field(..., description="OPEN или CLOSED")


# ==================== MAPPERS ====================

def visit_domain_to_response(visit: Visit) -> VisitResponse:
    """Маппер из доменной сущности в Response (для POST)."""
    return VisitResponse(
        id=visit.id,
        external_id=visit.external_id,
        client_id=visit.client_id,
        club_id=visit.club_id,
        entered_at=visit.entered_at,
        exited_at=visit.exited_at,
        status="CLOSED" if visit.exited_at else "OPEN",
    )


def visit_read_model_to_response(visit: VisitReadModel) -> VisitResponse:
    """Маппер из Read-модели в Response (для GET)."""
    return VisitResponse(
        id=visit.id,
        external_id=visit.external_id,
        client_id=visit.client_id,
        club_id=visit.club_id,
        entered_at=visit.entered_at,
        exited_at=visit.exited_at,
        status="CLOSED" if visit.exited_at else "OPEN",
    )