from passlib.context import CryptContext

from src.modules.users.application.ports.password_hasher import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
        )

    def hash(self, raw_password: str) -> str:
        return self._context.hash(raw_password)

    def verify(self, raw_password: str, password_hash: str) -> bool:
        return self._context.verify(raw_password, password_hash)
