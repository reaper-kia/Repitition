from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.modules.club.domain.value_objects import City, ClubName


@dataclass
class Club:
    """Клуб сети и граница доступа управляющего.

    Club не владеет клиентами, визитами, скидками или прогрессом.
    Он хранит только данные клуба, его активность и назначенного управляющего.
    """

    name: ClubName
    city: City
    manager_user_id: UUID | None = None
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def create(
        cls,
        name: ClubName,
        city: City,
        manager_user_id: UUID | None = None,
    ) -> "Club":
        return cls(
            name=name,
            city=city,
            manager_user_id=manager_user_id,
        )

    def assign_manager(self, user_id: UUID) -> None:
        self.manager_user_id = user_id

    def is_managed_by(self, user_id: UUID) -> bool:
        return self.manager_user_id == user_id
