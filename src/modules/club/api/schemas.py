from uuid import UUID

from pydantic import BaseModel, Field

from src.modules.club.application.read_models import ClubReadModel
from src.modules.club.domain.entities import Club


class CreateClubRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=120)
    manager_user_id: UUID | None = None


class UpdateManagerRequest(BaseModel):
    manager_user_id: UUID


class ClubResponse(BaseModel):
    id: UUID
    name: str
    city: str
    manager_user_id: UUID | None
    is_active: bool

    @classmethod
    def from_entity(cls, club: Club) -> "ClubResponse":
        return cls(
            id=club.id,
            name=club.name.value,
            city=club.city.value,
            manager_user_id=club.manager_user_id,
            is_active=club.is_active,
        )

    @classmethod
    def from_read_model(cls, club: ClubReadModel) -> "ClubResponse":
        return cls(
            id=club.id,
            name=club.name,
            city=club.city,
            manager_user_id=club.manager_user_id,
            is_active=club.is_active,
        )
