from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetClubQuery:
    club_id: UUID