from pydantic import BaseModel, Field, UUID4
from src.modules.club.domain.entities import Club
from src.modules.club.application.ports.club_read_repository import ClubScope


class ClubResponse(BaseModel):
    id: UUID4
    name: str
    city: str
    manager_user_id: UUID4 | None
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
    def from_scope(cls, scope: ClubScope) -> "ClubResponse":
        return cls(
            id=scope.club_id,
            name="",  # scope не содержит name и city, поэтому для списка нужно другое решение
            city="",
            manager_user_id=scope.manager_user_id,
            is_active=scope.is_active,
        )


class CreateClubRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=120)
    manager_user_id: UUID4 | None = None


class UpdateManagerRequest(BaseModel):
    manager_user_id: UUID4