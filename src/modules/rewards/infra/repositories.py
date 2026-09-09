from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.client.domain.enums import PurchaseType
from src.modules.rewards.domain.enums import (
    GrantPurpose,
    GrantStatus,
    ReservationSourceType,
    ReservationStatus,
)
from src.modules.rewards.application.ports.reward_repository import RewardRepository
from src.modules.rewards.domain.entities import (
    BudgetReservation,
    DiscountGrant,
    RewardBudget,
)
from src.modules.rewards.infra.models import (
    BudgetReservationModel,
    DiscountGrantModel,
    RewardBudgetModel,
)


class SQLAlchemyRewardRepository(RewardRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---------- бюджет ----------
    async def get_budget_for_update(
        self, club_id: UUID, budget_month: date
    ) -> RewardBudget | None:
        stmt = (
            select(RewardBudgetModel)
            .where(
                RewardBudgetModel.club_id == club_id,
                RewardBudgetModel.budget_month == budget_month,
            )
            .with_for_update()
        )
        row = await self._session.scalar(stmt)
        return self._to_budget(row) if row else None

    async def get_budget_by_id_for_update(self, budget_id: UUID) -> RewardBudget | None:
        stmt = (
            select(RewardBudgetModel)
            .where(RewardBudgetModel.id == budget_id)
            .with_for_update()
        )
        row = await self._session.scalar(stmt)
        return self._to_budget(row) if row else None

    async def save_budget(self, budget: RewardBudget) -> None:
        row = await self._session.get(RewardBudgetModel, budget.id)
        if row is None:
            raise RuntimeError(
                f"RewardBudgetModel {budget.id} vanished mid-transaction"
            )
        row.reserved = budget.reserved
        row.spent = budget.spent
        row.released = budget.released
        row.version = budget.version

    # ---------- резервация ----------
    async def get_reservation_by_idempotency_key(
        self, idempotency_key: str
    ) -> BudgetReservation | None:
        stmt = select(BudgetReservationModel).where(
            BudgetReservationModel.idempotency_key == idempotency_key
        )
        row = await self._session.scalar(stmt)
        return self._to_reservation(row) if row else None

    async def get_reservation_for_update(
        self, reservation_id: UUID
    ) -> BudgetReservation | None:
        stmt = (
            select(BudgetReservationModel)
            .where(BudgetReservationModel.id == reservation_id)
            .with_for_update()
        )
        row = await self._session.scalar(stmt)
        return self._to_reservation(row) if row else None

    async def add_reservation(self, reservation: BudgetReservation) -> None:
        self._session.add(self._from_reservation(reservation))

    async def save_reservation(self, reservation: BudgetReservation) -> None:
        row = await self._session.get(BudgetReservationModel, reservation.id)
        if row is None:
            raise RuntimeError(
                f"BudgetReservationModel {reservation.id} vanished mid-transaction"
            )
        row.consumed_amount = reservation.consumed_amount
        row.status = reservation.status

    # ---------- грант ----------
    async def get_grant_by_source_key(self, source_key: str) -> DiscountGrant | None:
        stmt = select(DiscountGrantModel).where(
            DiscountGrantModel.source_key == source_key
        )
        row = await self._session.scalar(stmt)
        return self._to_grant(row) if row else None

    async def add_grant(self, grant: DiscountGrant) -> None:
        self._session.add(self._from_grant(grant))

    # ---------- маппинг ORM -> домен ----------
    @staticmethod
    def _to_budget(row: RewardBudgetModel) -> RewardBudget:
        return RewardBudget(
            id=row.id,
            club_id=row.club_id,
            budget_month=row.budget_month,
            revenue_base=row.revenue_base,
            configured_limit=row.configured_limit,
            reserved=row.reserved,
            spent=row.spent,
            released=row.released,
            version=row.version,
        )

    @staticmethod
    def _to_reservation(row: BudgetReservationModel) -> BudgetReservation:
        return BudgetReservation(
            id=row.id,
            budget_id=row.budget_id,
            source_type=ReservationSourceType(row.source_type),  # ← оборачиваем
            source_id=row.source_id,
            reserved_amount=row.reserved_amount,
            consumed_amount=row.consumed_amount,
            idempotency_key=row.idempotency_key,
            status=ReservationStatus(row.status),  # ← оборачиваем
            created_at=row.created_at,
        )

    @staticmethod
    def _to_grant(row: DiscountGrantModel) -> DiscountGrant:
        return DiscountGrant(
            id=row.id,
            client_id=row.client_id,
            reservation_id=row.reservation_id,
            amount=row.amount,
            purpose=GrantPurpose(row.purpose),
            applicable_purchase_type=PurchaseType(row.applicable_purchase_type),
            source_key=row.source_key,
            valid_until=row.valid_until,
            status=GrantStatus(row.status),
            created_at=row.created_at,
            redeemed_at=row.redeemed_at,
        )

    # ---------- маппинг домен -> ORM ----------
    @staticmethod
    def _from_reservation(r: BudgetReservation) -> BudgetReservationModel:
        return BudgetReservationModel(
            id=r.id,
            budget_id=r.budget_id,
            source_type=r.source_type,
            source_id=r.source_id,
            reserved_amount=r.reserved_amount,
            consumed_amount=r.consumed_amount,
            idempotency_key=r.idempotency_key,
            status=r.status,
            created_at=r.created_at,
        )

    @staticmethod
    def _from_grant(g: DiscountGrant) -> DiscountGrantModel:
        return DiscountGrantModel(
            id=g.id,
            client_id=g.client_id,
            reservation_id=g.reservation_id,
            amount=g.amount,
            purpose=g.purpose,
            applicable_purchase_type=g.applicable_purchase_type,
            source_key=g.source_key,
            valid_until=g.valid_until,
            status=g.status,
            created_at=g.created_at,
            redeemed_at=g.redeemed_at,
        )
