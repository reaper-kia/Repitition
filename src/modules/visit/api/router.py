# src/modules/visit/api/router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID

from src.modules.visit.api.schemas import (
    RecordVisitRequest,
    CloseVisitRequest,
    VisitResponse,
    visit_domain_to_response,
    visit_read_model_to_response,
)
from src.modules.visit.api.dependencies import (
    get_record_visit_handler,
    get_close_visit_handler,
    get_current_club_visits_handler,
    get_client_visits_history_handler,
)
from src.modules.visit.application.commands.record_visit import RecordVisitCommand
from src.modules.visit.application.commands.close_visit import CloseVisitCommand
from src.modules.visit.application.queries.get_current_club_visits import GetCurrentClubVisitsQuery
from src.modules.visit.application.queries.get_client_visits_history import GetClientVisitsHistoryQuery

from src.modules.visit.domain.exceptions import (
    VisitNotFoundError,
    VisitAlreadyClosedError,
    InvalidVisitPeriodError,
    ClientSnapshotNotFoundError,
)

router = APIRouter(prefix="/api/v1", tags=["Visits"])


# ============================================
# WRITE: Эндпоинты для турникета (или его адаптера)
# ============================================

@router.post(
    "/visits/record",
    response_model=VisitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать вход клиента"
)
async def record_visit(
    data: RecordVisitRequest,
    handler=Depends(get_record_visit_handler),
):
    cmd = RecordVisitCommand(
        external_id=data.external_id,
        client_id=data.client_id,
        club_id=data.club_id,
        entered_at=data.entered_at,
    )
    try:
        visit = await handler.handle(cmd)
        return visit_domain_to_response(visit)
    except ClientSnapshotNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidVisitPeriodError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/visits/close",
    response_model=VisitResponse,
    summary="Зарегистрировать выход клиента"
)
async def close_visit(
    data: CloseVisitRequest,
    handler=Depends(get_close_visit_handler),
):
    cmd = CloseVisitCommand(
        external_id=data.external_id,
        exited_at=data.exited_at,
    )
    try:
        visit = await handler.handle(cmd)
        return visit_domain_to_response(visit)
    except VisitNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VisitAlreadyClosedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidVisitPeriodError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# ============================================
# READ: Эндпоинты для админки / личного кабинета
# ============================================

@router.get(
    "/clubs/{club_id}/visits/current",
    response_model=list[VisitResponse],
    summary="Кто сейчас находится в клубе"
)
async def get_current_club_visits(
    club_id: UUID,
    handler=Depends(get_current_club_visits_handler),
):
    query = GetCurrentClubVisitsQuery(club_id=club_id)
    visits = await handler.handle(query)
    return [visit_read_model_to_response(v) for v in visits]


@router.get(
    "/clients/{client_id}/visits/history",
    response_model=list[VisitResponse],
    summary="История посещений клиента"
)
async def get_client_visits_history(
    client_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler=Depends(get_client_visits_history_handler),
):
    query = GetClientVisitsHistoryQuery(
        client_id=client_id,
        page=page,
        page_size=page_size,
    )
    # Хендлер возвращает кортеж (items, total), но для простоты списка отдадим только items
    # Если нужна пагинация с total, нужно создать VisitPageResponse
    items, total = await handler.handle(query)
    return [visit_read_model_to_response(v) for v in items]