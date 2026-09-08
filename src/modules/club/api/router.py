from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from src.modules.auth.api.dependencies import get_current_user_id, get_current_user
from src.modules.club.api.schemas import ClubResponse, CreateClubRequest, UpdateManagerRequest
from src.modules.club.api.dependencies import (
    get_create_club_handler,
    get_update_club_manager_handler,
    get_list_clubs_handler,
    get_get_club_handler,
)
from src.modules.club.application.commands.create_club import CreateClubCommand
from src.modules.club.application.commands.update_club_manager import UpdateClubManagerCommand
from src.modules.club.application.queries.list_clubs import ListClubsQuery
from src.modules.club.application.queries.get_club_by_id import GetClubByIdQuery
from src.modules.club.domain.exceptions import (
    ClubNotFoundError,
    ManagerUserNotFoundError,
    ManagerUserNotClubManagerError,
    InvalidClubNameError,
    InvalidCityError,
)
from src.modules.users.domain.entities import User


router = APIRouter(prefix="/api/v1/clubs", tags=["Club"])


# ---- Зависимость для проверки прав администратора сети ----
async def require_network_admin(user: User = Depends(get_current_user)) -> None:
    """
    Проверяет, что текущий пользователь имеет права администратора сети.
    Если нет – выбрасывает 403 Forbidden.
    """
    # Вариант 1: если в User есть поле role
    if hasattr(user, "role") and user.role == "NETWORK_ADMIN":
        return
    # Вариант 2: если в User есть поле is_admin (как в кофейне)
    if hasattr(user, "is_admin") and user.is_admin:
        return
    # Если ни одно не подошло – доступ запрещён
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Требуются права администратора сети"
    )


# ---- Эндпоинты ----

@router.post("/", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
async def create_club(
    data: CreateClubRequest,
    handler=Depends(get_create_club_handler),
    _=Depends(require_network_admin),
):
    """
    Создание нового клуба. Доступно только администратору сети.
    """
    try:
        club = await handler.handle(
            CreateClubCommand(
                name=data.name,
                city=data.city,
                manager_user_id=data.manager_user_id,
            )
        )
    except (InvalidClubNameError, InvalidCityError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except (ManagerUserNotFoundError, ManagerUserNotClubManagerError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ClubResponse.from_entity(club)


@router.get("/", response_model=list[ClubResponse])
async def list_clubs(
    handler=Depends(get_list_clubs_handler),
    _=Depends(get_current_user_id),  # любой авторизованный пользователь
):
    """
    Список всех клубов. Доступен любому авторизованному пользователю.
    """
    scopes = await handler.handle(ListClubsQuery())
    # Для списка используем отдельный метод, возвращающий только id и is_active
    # В реальности нужно было бы вернуть полные данные, но для простоты пока так
    return [ClubResponse.from_scope(s) for s in scopes]


@router.get("/{club_id}", response_model=ClubResponse)
async def get_club(
    club_id: UUID,
    handler=Depends(get_get_club_handler),
    _=Depends(get_current_user_id),
):
    """
    Получение информации о клубе по ID. Доступно любому авторизованному.
    """
    try:
        club = await handler.handle(GetClubByIdQuery(club_id=club_id))
    except ClubNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ClubResponse.from_entity(club)


@router.patch("/{club_id}/manager", response_model=ClubResponse)
async def update_club_manager(
    club_id: UUID,
    data: UpdateManagerRequest,
    handler=Depends(get_update_club_manager_handler),
    _=Depends(require_network_admin),
):
    """
    Назначение менеджера клуба. Доступно только администратору сети.
    """
    try:
        club = await handler.handle(
            UpdateClubManagerCommand(
                club_id=club_id,
                manager_user_id=data.manager_user_id,
            )
        )
    except ClubNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ManagerUserNotFoundError, ManagerUserNotClubManagerError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ClubResponse.from_entity(club)