from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class ListClientsByClubQuery:
    client_id: UUID  
    
    page: int = 1
    page_size: int = 20