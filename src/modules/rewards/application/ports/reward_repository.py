from datetime import date
from typing import Protocol
from uuid import UUID

from src.modules.rewards.domain.entities import (
    BudgetReservation,
    DiscountGrant,
    RewardBudget,
)


class RewardRepository(Protocol):
    # --- бюджет ---
    async def get_budget_for_update(
        self, club_id: UUID, budget_month: date
    ) -> RewardBudget | None:
        """Достать бюджет клуба ЗА месяц С БЛОКИРОВКОЙ строки (SELECT FOR UPDATE).

        Блокировка держится до конца транзакции. Второй параллельный резерв
        по этому же бюджету будет ждать здесь, потом перечитает свежие цифры.
        """
        ...

    async def get_budget_by_id_for_update(
        self, budget_id: UUID
    ) -> RewardBudget | None:
        """Бюджет по id с блокировкой — нужен на потреблении,
        когда club_id неизвестен, а есть только budget_id из резервации."""
        ...

    async def save_budget(self, budget: RewardBudget) -> None:
        """Записать изменённые reserved/spent/version обратно в строку."""
        ...

    # --- резервация ---
    async def get_reservation_by_idempotency_key(
        self, idempotency_key: str
    ) -> BudgetReservation | None:
        """Для идемпотентности: повтор с тем же ключом вернёт существующую бронь."""
        ...

    async def get_reservation_for_update(
        self, reservation_id: UUID
    ) -> BudgetReservation | None:
        """Достать бронь с блокировкой — нужно на потреблении (TL-05)."""
        ...

    async def add_reservation(self, reservation: BudgetReservation) -> None:
        ...

    async def save_reservation(self, reservation: BudgetReservation) -> None:
        ...

    # --- грант ---
    async def get_grant_by_source_key(self, source_key: str) -> DiscountGrant | None:
        """Для ALREADY_GRANTED: если грант с таким ключом уже есть — вернуть его."""
        ...

    async def add_grant(self, grant: DiscountGrant) -> None:
        ...