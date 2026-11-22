
import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.producer import (
    OrderCreatedEventPayload,
    OrderProductEventItem,
    publish_order_created_event,
)


def make_payload() -> OrderCreatedEventPayload:
    return OrderCreatedEventPayload(
        event_id=uuid.uuid4(),
        total_amount=3,
        total_price=30.0,
        products=[OrderProductEventItem(id=uuid.uuid4(), quantity=3)],
        event_date=date(2026, 1, 1),
        user_email="alice@example.com",
    )


def test_order_created_event_payload_parses_product_ids() -> None:
    product_id = uuid.uuid4()

    payload = OrderCreatedEventPayload(
        event_id=str(uuid.uuid4()),
        total_amount=2,
        total_price=20.0,
        products=[{"id": str(product_id), "quantity": 2}],
        event_date="2026-01-01",
        user_email="alice@example.com",
    )

    assert isinstance(payload.event_id, uuid.UUID)
    assert payload.products[0].id == product_id
    assert payload.event_date == date(2026, 1, 1)


async def test_publish_order_created_event(monkeypatch) -> None:
    publish = AsyncMock()
    monkeypatch.setattr(
        "src.producer.order_created_publisher",
        SimpleNamespace(publish=publish),
    )
    payload = make_payload()

    await publish_order_created_event(payload)

    publish.assert_awaited_once_with(payload)
