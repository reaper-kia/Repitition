from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.modules.client.domain.enums import (
    AcquisitionChannel,
    ClientStatus,
    PurchaseType,
)
from src.modules.client.domain.exceptions import (
    ReferrerAlreadySetError,
    SelfReferralError,
)
from src.modules.client.domain.value_objects import Membership, ReferralCode


@dataclass
class Client:
    """Бизнес-профиль клиента. Владелец — Client Module.

    НЕ хранит: баллы, число визитов, ранг, накопленные скидки — всё это
    вычисляется другими модулями из своих данных.

    display_name дублирует User.name намеренно: панель управляющего
    показывает списки клиентов, и джойн через Identity на каждую карточку
    не окупается. Обновляется по событию из Identity при смене имени.
    """

    user_id: UUID
    club_id: UUID
    display_name: str
    membership: Membership
    referral_code: ReferralCode
    acquisition_channel: AcquisitionChannel = AcquisitionChannel.ORGANIC
    referred_by_client_id: UUID | None = None
    status: ClientStatus = ClientStatus.ACTIVE
    registered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def register(
        cls,
        user_id: UUID,
        club_id: UUID,
        display_name: str,
        membership: Membership,
        referral_code: ReferralCode,
        acquisition_channel: AcquisitionChannel = AcquisitionChannel.ORGANIC,
    ) -> "Client":
        return cls(
            user_id=user_id,
            club_id=club_id,
            display_name=display_name,
            membership=membership,
            referral_code=referral_code,
            acquisition_channel=acquisition_channel,
        )

    def attach_referrer(self, referrer_client_id: UUID) -> None:
        """Инварианты реферала живут здесь, а не в обработчике:
        их нарушение — это нарушение целостности домена, а не валидация ввода."""
        if referrer_client_id == self.id:
            raise SelfReferralError("Client cannot refer themselves")
        if self.referred_by_client_id is not None:
            raise ReferrerAlreadySetError("Referrer is already attached")
        self.referred_by_client_id = referrer_client_id
        self.acquisition_channel = AcquisitionChannel.REFERRAL

    def apply_renewal(self, months: int) -> None:
        self.membership = self.membership.extended_by(months)
        self.status = ClientStatus.ACTIVE

    def refresh_status(self, at: datetime | None = None) -> None:
        if self.status is ClientStatus.BLOCKED:
            return
        self.status = (
            ClientStatus.ACTIVE
            if self.membership.is_active(at)
            else ClientStatus.EXPIRED
        )


@dataclass
class Purchase:
    """Неизменяемый подтверждённый факт покупки.

    В MVP создаётся по кнопке управляющего — это симулятор внешней кассы,
    а не платёжный шлюз. Данные карты здесь не появляются никогда.

    idempotency_key защищает от двойного создания при повторе команды:
    вторая покупка не создаётся и вторая реферальная награда не выдаётся.
    """

    client_id: UUID
    club_id: UUID
    type: PurchaseType
    gross_amount: Decimal
    discount_amount: Decimal
    confirmed_by_user_id: UUID
    idempotency_key: str
    confirmed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)

    @property
    def paid_amount(self) -> Decimal:
        return self.gross_amount - self.discount_amount

    @classmethod
    def confirm(
        cls,
        client_id: UUID,
        club_id: UUID,
        type: PurchaseType,
        gross_amount: Decimal,
        discount_amount: Decimal,
        confirmed_by_user_id: UUID,
        idempotency_key: str,
    ) -> "Purchase":
        if gross_amount < 0 or discount_amount < 0:
            raise ValueError("Amounts must not be negative")
        if discount_amount > gross_amount:
            raise ValueError("Discount must not exceed gross amount")
        return cls(
            client_id=client_id,
            club_id=club_id,
            type=type,
            gross_amount=gross_amount,
            discount_amount=discount_amount,
            confirmed_by_user_id=confirmed_by_user_id,
            idempotency_key=idempotency_key,
        )

    def is_first_membership(self) -> bool:
        return self.type is PurchaseType.MEMBERSHIP
