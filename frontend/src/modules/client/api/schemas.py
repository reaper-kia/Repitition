from uuid import UUID

from pydantic import BaseModel, Field


class CreateClientRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ClientResponse(BaseModel):
    id: UUID
    name: str
