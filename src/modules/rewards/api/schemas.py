from uuid import UUID

from pydantic import BaseModel, Field


class CreateRewardsRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class RewardsResponse(BaseModel):
    id: UUID
    name: str
