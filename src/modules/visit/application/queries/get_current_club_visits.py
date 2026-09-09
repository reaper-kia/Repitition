# src/modules/visit/application/queries/get_current_club_visits.py
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class GetCurrentClubVisitsQuery:
    """Запрос: кто сейчас находится в клубе (визиты без exited_at)."""
    club_id: UUID