from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from src.core.config import settings
from src.modules.auth.application.exceptions import InvalidTokenError
from src.modules.auth.application.ports.token_service import TokenService


class JwtTokenService(TokenService):
    def create_access_token(self, user_id: UUID) -> str:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)

        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": expires_at,
            "type": "access",
        }

        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    def decode_access_token(self, token: str) -> UUID:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise InvalidTokenError("Invalid token") from exc

        token_type = payload.get("type")
        if token_type != "access":
            raise InvalidTokenError("Invalid token type")

        subject = payload.get("sub")
        if subject is None:
            raise InvalidTokenError("Token subject is missing")

        try:
            return UUID(subject)
        except ValueError as exc:
            raise InvalidTokenError("Invalid token subject") from exc
