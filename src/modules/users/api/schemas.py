from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    admin_code: str | None = None


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_admin: bool
