from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.modules.auth.api.cookies import (
    delete_access_token_cookie,
    set_access_token_cookie,
)
from src.modules.auth.api.dependencies import get_auth_mediator
from src.modules.auth.api.rate_limit import limit_login_request
from src.modules.auth.api.schemas import AuthMessageResponse, LoginRequest
from src.modules.auth.application.commands.login_user import LoginUserCommand
from src.modules.auth.application.exceptions import InvalidCredentialError
from src.shared.application.mediator import Mediator

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(limit_login_request)],
)
async def login(
    request: LoginRequest,
    response: Response,
    mediator: Mediator = Depends(get_auth_mediator),
) -> AuthMessageResponse:
    cmd = LoginUserCommand(
        email=request.email,
        password=request.password,
    )

    try:
        access_token = await mediator.send(cmd)
    except InvalidCredentialError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    set_access_token_cookie(
        response=response,
        access_token=access_token,
    )

    return AuthMessageResponse(message="Logged in")


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def logout(response: Response) -> AuthMessageResponse:
    delete_access_token_cookie(response)

    return AuthMessageResponse(message="Logged out")
