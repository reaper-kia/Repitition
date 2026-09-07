"""Доменные события Client.

Событие — это запись о свершившемся факте, в прошедшем времени.
Оно содержит ровно те поля, которые нужны получателю, чтобы отреагировать,
и ничего сверх того.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class FirstMembershipPurchased:
    """Новичок оплатил первый абонемент.

    Получатель — Rewards: только теперь можно выдать награду пригласившему.
    До оплаты обещать реферальную скидку нельзя, иначе её можно фармить
    регистрациями без покупок.

    purchase_id используется как ключ идемпотентности при выдаче награды.
    """

    client_id: UUID
    club_id: UUID
    referred_by_client_id: UUID | None
    purchase_id: UUID
    occurred_at: datetime
