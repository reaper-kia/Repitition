from dataclasses import dataclass
from uuid import UUID

from pydantic import EmailStr


@dataclass(frozen=True)
class AuthUserReadModel:
    id: UUID
    email: EmailStr
    password_hash: str
