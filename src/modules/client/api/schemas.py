# src/modules/client/api/schemas.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from src.modules.client.domain.enums import MembershipType, ClientStatus
from src.modules.client.domain.entities import Client
from src.modules.client.application.read_models import ClientReadModel


# ==================== REQUEST ====================

class RegisterClientRequest(BaseModel):
    """Схема запроса на регистрацию клиента."""
    club_id: UUID
    membership_type: MembershipType
    referral_code: str | None = Field(default=None, max_length=16)


# ==================== RESPONSE ====================

class ClientResponse(BaseModel):
    """Схема ответа с данными клиента."""
    id: UUID
    display_name: str
    club_id: UUID
    membership_type: MembershipType
    membership_expires_at: datetime
    referral_code: str
    status: ClientStatus
    
    # Поле заведено сразу для фронта, чтобы не менять DTO в B2-07
    referral_discount_promised: bool = False 


# ==================== MAPPERS ====================

def client_to_response(client: Client) -> ClientResponse:
    """Маппер из доменной сущности в Response (для POST)."""
    return ClientResponse(
        id=client.id,
        display_name=client.display_name,
        club_id=client.club_id,
        membership_type=client.membership.type,
        membership_expires_at=client.membership.expires_at,
        referral_code=client.referral_code.value,
        status=client.status,
        referral_discount_promised=False,
    )

def client_read_model_to_response(client: ClientReadModel) -> ClientResponse:
    """Маппер из Read-модели в Response (для GET)."""
    return ClientResponse(
        id=client.id,
        display_name=client.display_name,
        club_id=client.club_id,
        membership_type=client.membership_type,
        membership_expires_at=client.membership_expires_at,
        referral_code=client.referral_code,
        status=client.status,
        referral_discount_promised=False,
    )