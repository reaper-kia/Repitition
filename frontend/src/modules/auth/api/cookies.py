from fastapi import Response

from src.core.config import settings


def set_access_token_cookie(
    response: Response,
    access_token: str,
) -> None:
    response.set_cookie(
        key=settings.auth_access_cookie_name,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=settings.auth_cookie_httponly,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path=settings.auth_cookie_path,
    )


def delete_access_token_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_access_cookie_name,
        path=settings.auth_cookie_path,
    )
