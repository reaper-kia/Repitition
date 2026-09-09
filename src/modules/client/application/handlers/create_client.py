from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.modules.client.application.commands.create_client import (
    CreateClientCommand,
)
from src.modules.client.domain.entities import Client
from src.modules.client.domain.enums import MembershipType
from src.modules.client.domain.exceptions import (
    ClientAlreadyExistsError,
    ClubInactiveError,
    InvalidReferralCodeError,
    ReferralCodeGenerationError,
)
from src.modules.client.domain.value_objects import Membership, ReferralCode
from src.shared.application.unit_of_work import UnitOfWorkFactory

_MEMBERSHIP_MONTHS = {
    MembershipType.ONE_MONTH: 1,
    MembershipType.THREE_MONTHS: 3,
    MembershipType.SIX_MONTHS: 6,
    MembershipType.TWELVE_MONTHS: 12,
}

_REFERRAL_CODE_ATTEMPTS = 5


@dataclass
class CreateClientHandler:
    uow_factory: UnitOfWorkFactory

    async def handle(self, cmd: CreateClientCommand) -> Client:
        async with self.uow_factory() as uow:
            club_scope = await uow.club_snapshots.get_scope(cmd.club_id)

            if club_scope is None or not club_scope.is_active:
                raise ClubInactiveError("Cannot register in an inactive club")

            existing_client = await uow.clients.get_by_user_id(cmd.user_id)

            if existing_client is not None:
                raise ClientAlreadyExistsError("User is already registered as a client")

            referrer_id: UUID | None = None

            if cmd.referral_code is not None:
                referrer = await uow.clients.get_by_referral_code(cmd.referral_code)

                if referrer is None:
                    raise InvalidReferralCodeError("Referral code does not exist")

                referrer_id = referrer.id

            referral_code: ReferralCode | None = None

            for _ in range(_REFERRAL_CODE_ATTEMPTS):
                candidate = ReferralCode.generate()
                collision = await uow.clients.get_by_referral_code(candidate.value)

                if collision is None:
                    referral_code = candidate
                    break

            if referral_code is None:
                raise ReferralCodeGenerationError(
                    "Failed to generate a unique referral code " "after 5 attempts"
                )

            membership = Membership(
                type=cmd.membership_type,
                expires_at=datetime.now(UTC),
            ).extended_by(_MEMBERSHIP_MONTHS[cmd.membership_type])

            client = Client.register(
                user_id=cmd.user_id,
                club_id=cmd.club_id,
                display_name=cmd.display_name,
                membership=membership,
                referral_code=referral_code,
            )

            if referrer_id is not None:
                client.attach_referrer(referrer_id)

            await uow.clients.add(client)
            await uow.commit()

        return client
