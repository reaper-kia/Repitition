from dataclasses import dataclass


@dataclass
class RegisterUserCommand:
    name: str
    email: str
    password: str
    admin_code: str | None = None
