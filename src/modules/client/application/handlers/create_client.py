from datetime import datetime, UTC
from uuid import UUID

from src.modules.client.application.commands.create_client import CreateClientCommand
from src.modules.client.domain.entities import Client
from src.modules.client.domain.enums import MembershipType
from src.modules.client.domain.exceptions import (
    ClubInactiveError,
    ClientAlreadyExistsError,
    InvalidReferralCodeError,
    ReferralCodeGenerationError,
)
from src.modules.client.domain.value_objects import Membership, ReferralCode
from src.shared.application.unit_of_work import UnitOfWork

# Маппинг типов абонемента в количество месяцев
_MEMBERSHIP_MONTHS = {
    MembershipType.ONE_MONTH: 1,
    MembershipType.THREE_MONTHS: 3,
    MembershipType.SIX_MONTHS: 6,
    MembershipType.TWELVE_MONTHS: 12,
}

class CreateClientHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, cmd: CreateClientCommand) -> Client:
        async with self._uow as uow:
            # 1. Проверка активности клуба (через Snapshot)
            club_scope = await uow.club_snapshots.get_scope(cmd.club_id)
            if not club_scope or not club_scope.is_active:
                raise ClubInactiveError("Cannot register in an inactive club")

            # 2. Проверка уникальности пользователя (user_id UNIQUE)
            existing_client = await uow.clients.get_by_user_id(cmd.user_id)
            if existing_client:
                raise ClientAlreadyExistsError("User is already registered as a client")

            # 3. Обработка реферального кода (если передан)
            referrer_id: UUID | None = None
            if cmd.referral_code:
                referrer = await uow.clients.get_by_referral_code(cmd.referral_code)
                if not referrer:
                    raise InvalidReferralCodeError("Referral code does not exist")
                referrer_id = referrer.id

            # 4. Генерация уникального реферального кода для нового клиента
            # ТЗ: "при коллизии UNIQUE — перегенерировать, до 5 попыток, потом 500"
            new_referral_code: ReferralCode | None = None
            for _ in range(5):
                candidate = ReferralCode.generate()
                collision = await uow.clients.get_by_referral_code(candidate.value)
                if not collision:
                    new_referral_code = candidate
                    break
            
            if not new_referral_code:
                raise ReferralCodeGenerationError("Failed to generate unique referral code after 5 attempts")

            # 5. Формирование Value Objects и создание Агрегата
            base_membership = Membership(type=cmd.membership_type, expires_at=datetime.now(UTC))
            months = _MEMBERSHIP_MONTHS.get(cmd.membership_type, 1)
            membership = base_membership.extended_by(months)

            client = Client.register(
                user_id=cmd.user_id,
                club_id=cmd.club_id,
                display_name=cmd.display_name,
                membership=membership,
                referral_code=new_referral_code,
            )

            # Инвариант реферала живёт в домене (attach_referrer)
            if referrer_id:
                client.attach_referrer(referrer_id)

            # 6. Сохранение и коммит
            await uow.clients.add(client)
            await uow.commit()

            return client