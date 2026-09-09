from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.auth.api.actor import RequestActor
from src.modules.auth.api.dependencies import get_current_actor, require_roles
from src.modules.club.api.dependencies import (
    get_club_handler,
    get_create_club_handler,
    get_list_clubs_handler,
    get_update_club_manager_handler,
)
from src.modules.club.api.schemas import (
    ClubResponse,
    CreateClubRequest,
    UpdateManagerRequest,
)
from src.modules.club.application.commands.create_club import CreateClubCommand
from src.modules.club.application.commands.update_club_manager import (
    UpdateClubManagerCommand,
)
from src.modules.club.application.handlers.create_club import CreateClubHandler
from src.modules.club.application.handlers.get_club_by_id import GetClubHandler
from src.modules.club.application.handlers.list_clubs import ListClubsHandler
from src.modules.club.application.handlers.update_club_manager import (
    UpdateClubManagerHandler,
)
from src.modules.club.application.queries.get_club_by_id import GetClubByIdQuery
from src.modules.club.application.queries.list_clubs import ListClubsQuery
from src.modules.club.domain.exceptions import (
    ClubNotFoundError,
    InvalidCityError,
    InvalidClubNameError,
    ManagerUserNotClubManagerError,
    ManagerUserNotFoundError,
)
from src.modules.users.domain.enums import Role

router = APIRouter(prefix="/api/v1/clubs", tags=["Club"])


@router.post(
    "",
    response_model=ClubResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(Role.NETWORK_ADMIN))],
)
async def create_club(
    data: CreateClubRequest,
    handler: CreateClubHandler = Depends(get_create_club_handler),
) -> ClubResponse:
    try:
        club = await handler.handle(
            CreateClubCommand(
                name=data.name,
                city=data.city,
                manager_user_id=data.manager_user_id,
            )
        )
    except (InvalidClubNameError, InvalidCityError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except (
        ManagerUserNotFoundError,
        ManagerUserNotClubManagerError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ClubResponse.from_entity(club)


@router.get("", response_model=list[ClubResponse])
async def list_clubs(
    _actor: RequestActor = Depends(get_current_actor),
    handler: ListClubsHandler = Depends(get_list_clubs_handler),
) -> list[ClubResponse]:
    clubs = await handler.handle(ListClubsQuery())
    return [ClubResponse.from_read_model(club) for club in clubs]


@router.get("/{club_id}", response_model=ClubResponse)
async def get_club(
    club_id: UUID,
    _actor: RequestActor = Depends(get_current_actor),
    handler: GetClubHandler = Depends(get_club_handler),
) -> ClubResponse:
    try:
        club = await handler.handle(GetClubByIdQuery(id=club_id))
    except ClubNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ClubResponse.from_entity(club)


@router.patch(
    "/{club_id}/manager",
    response_model=ClubResponse,
    dependencies=[Depends(require_roles(Role.NETWORK_ADMIN))],
)
async def update_club_manager(
    club_id: UUID,
    data: UpdateManagerRequest,
    handler: UpdateClubManagerHandler = Depends(get_update_club_manager_handler),
) -> ClubResponse:
    try:
        club = await handler.handle(
            UpdateClubManagerCommand(
                club_id=club_id,
                manager_user_id=data.manager_user_id,
            )
        )
    except ClubNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (
        ManagerUserNotFoundError,
        ManagerUserNotClubManagerError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ClubResponse.from_entity(club)
