from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.modules.club.domain.value_objects import City


@dataclass
class Club:
    """Клуб сети. Задаёт организационную принадлежность и область доступа.

    НЕ владеет клиентами, визитами, скидками и прогрессом механик —
    только тем, кто им управляет и активен ли он.
    """

    name: str
    city: City
    manager_user_id: UUID | None = None
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def create(
        cls, name: str, city: City, manager_user_id: UUID | None = None
    ) -> "Club":
        return cls(name=name, city=city, manager_user_id=manager_user_id)

    def assign_manager(self, user_id: UUID) -> None:
        self.manager_user_id = user_id

    def is_managed_by(self, user_id: UUID) -> bool:
        """Проверка области доступа. Вызывается Club-модулем, а не Identity:
        Identity знает роль, но не знает привязку к конкретному клубу."""
        return self.manager_user_id == user_id
