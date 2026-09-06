from uuid import UUID

from pydantic import BaseModel, Field


class CreateAchivementRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class AchivementResponse(BaseModel):
    id: UUID
    name: str
