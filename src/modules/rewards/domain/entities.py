from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.modules.client.domain.enums import PurchaseType
from src.modules.rewards.domain.enums import (
    GrantPurpose,
    GrantStatus,
    ReservationSourceType,
    ReservationStatus,
)
from src.modules.rewards.domain.exceptions import (
    GrantAlreadyRedeemedError,
    GrantNotApplicableError,
    InsufficientBudgetError,
    InvalidRewardAmountError,
    ReservationExhaustedError,
    ReservationNotActiveError,
)

STATUTORY_LIMIT_RATIO = Decimal("0.04")


@dataclass
class RewardBudget:
    """Месячный фонд конкретного клуба.

    limit = min(configured_limit, revenue_base * 0.04)

    revenue_base — подтверждённая выручка ЗАКРЫТОГО месяца M-1. Так фонд
    месяца M известен заранее и не плавает по ходу месяца.

    Главный инвариант всей системы: reserved + spent <= limit.
    Он защищается транзакцией + optimistic version + CHECK constraint
    в БД. Ни Engagement, ни Client не могут его обойти — выдать скидку
    можно только через этот модуль.
    """

    club_id: UUID
    budget_month: date
    revenue_base: Decimal
    configured_limit: Decimal
    reserved: Decimal = Decimal("0")
    spent: Decimal = Decimal("0")
    released: Decimal = Decimal("0")
    version: int = 0
    id: UUID = field(default_factory=uuid4)

    @property
    def statutory_limit(self) -> Decimal:
        return self.revenue_base * STATUTORY_LIMIT_RATIO

    @property
    def limit(self) -> Decimal:
        return min(self.configured_limit, self.statutory_limit)

    @property
    def available(self) -> Decimal:
        return self.limit - self.reserved - self.spent

    def reserve(self, amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidRewardAmountError("Amount must be positive")
        if amount > self.available:
            raise InsufficientBudgetError(
                f"Requested {amount}, available {self.available}"
            )
        self.reserved += amount
        self.version += 1

    def consume(self, amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidRewardAmountError("Amount must be positive")
        if amount > self.reserved:
            raise ReservationExhaustedError("Consuming more than reserved")
        self.reserved -= amount
        self.spent += amount
        self.version += 1

    def release(self, amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidRewardAmountError("Amount must be positive")
        if amount > self.reserved:
            raise ReservationExhaustedError("Releasing more than reserved")
        self.reserved -= amount
        self.released += amount
        self.version += 1


@dataclass
class BudgetReservation:
    """Финансовое обещание под будущую награду.

    Существует, чтобы не пришлось заворачивать Engagement и Rewards
    в одну общую транзакцию: резерв и трата разнесены во времени,
    иногда на дни.

    Для реферала резервируются ОБЕ стороны сразу — иначе сеть пообещает
    награду пригласившему и не сможет её выполнить.
    """

    budget_id: UUID
    source_type: ReservationSourceType
    source_id: UUID
    reserved_amount: Decimal
    idempotency_key: str
    consumed_amount: Decimal = Decimal("0")
    status: ReservationStatus = ReservationStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)

    @property
    def remaining(self) -> Decimal:
        return self.reserved_amount - self.consumed_amount

    def consume(self, amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidRewardAmountError("Amount must be positive")
        if self.status is not ReservationStatus.ACTIVE:
            raise ReservationNotActiveError(f"Reservation is {self.status}")
        if amount > self.remaining:
            raise ReservationExhaustedError(
                f"Requested {amount}, remaining {self.remaining}"
            )
        self.consumed_amount += amount
        if self.remaining == 0:
            self.status = ReservationStatus.CONSUMED


@dataclass
class DiscountGrant:
    """Персональное право клиента на скидку.

    source_key UNIQUE — защита от двойной выдачи. Повторная обработка
    того же события возвращает ALREADY_GRANTED, а не создаёт вторую скидку.

    Деньги — Decimal, никогда не float.
    """

    client_id: UUID
    reservation_id: UUID
    amount: Decimal
    purpose: GrantPurpose
    applicable_purchase_type: PurchaseType
    source_key: str
    valid_until: datetime
    status: GrantStatus = GrantStatus.AVAILABLE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    redeemed_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    def is_applicable(
        self, purchase_type: PurchaseType, at: datetime | None = None
    ) -> bool:
        moment = at or datetime.now(UTC)
        return (
            self.status is GrantStatus.AVAILABLE
            and self.applicable_purchase_type is purchase_type
            and self.valid_until > moment
        )

    def redeem(self, purchase_type: PurchaseType, at: datetime | None = None) -> None:
        """Погашение идёт в ОДНОЙ транзакции с созданием Purchase.
        Если что-то упало — откатывается и то и другое."""
        if self.status is GrantStatus.REDEEMED:
            raise GrantAlreadyRedeemedError("Grant is already redeemed")
        if not self.is_applicable(purchase_type, at):
            raise GrantNotApplicableError("Grant is not applicable to this purchase")
        self.status = GrantStatus.REDEEMED
        self.redeemed_at = at or datetime.now(UTC)

    def expire(self) -> None:
        if self.status is GrantStatus.AVAILABLE:
            self.status = GrantStatus.EXPIRED

    def cancel(self) -> None:
        if self.status is GrantStatus.AVAILABLE:
            self.status = GrantStatus.CANCELLED
