from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from src.shared.domain.exceptions import InvalidCurrencyError, NegativeAmountError
from src.shared.domain.value_objects import Money
from src.shared.events.integration_event import IntegrationEvent

AGGREGATE_ID = UUID("10000000-0000-0000-0000-000000000001")


@pytest.mark.unit
def test_money_normalizes_currency() -> None:
    money = Money(amount=Decimal("10.00"), currency=" rub ")
    assert money.currency == "RUB"


@pytest.mark.unit
@pytest.mark.parametrize("currency", ["", "BTC", "XYZ"])
def test_money_rejects_unsupported_currency(currency: str) -> None:
    with pytest.raises(InvalidCurrencyError):
        Money(amount=Decimal("1.00"), currency=currency)


@pytest.mark.unit
def test_money_rejects_negative_amount() -> None:
    with pytest.raises(NegativeAmountError):
        Money(amount=Decimal("-1.00"), currency="RUB")


@pytest.mark.unit
def test_integration_event_serializes_payload() -> None:
    event = IntegrationEvent(
        event_type="user.registered",
        data={"user_id": str(AGGREGATE_ID)},
        aggregate_type="user",
        aggregate_id=AGGREGATE_ID,
    )

    payload = event.to_payload()

    assert payload["event_type"] == "user.registered"
    assert payload["aggregate_type"] == "user"
    assert payload["aggregate_id"] == str(AGGREGATE_ID)
    assert payload["event_version"] == 1
    assert payload["payload"] == {"user_id": str(AGGREGATE_ID)}
    assert payload["metadata"] == {}
    assert datetime.fromisoformat(payload["occurred_at"]).tzinfo is not None


@pytest.mark.unit
def test_integration_event_defaults_are_unique() -> None:
    first = IntegrationEvent(
        event_type="a", data={}, aggregate_type="t", aggregate_id=AGGREGATE_ID
    )
    second = IntegrationEvent(
        event_type="a", data={}, aggregate_type="t", aggregate_id=AGGREGATE_ID
    )

    assert first.event_id != second.event_id
    assert first.occurred_at <= datetime.now(UTC)
