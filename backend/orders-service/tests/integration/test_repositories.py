
import uuid
from datetime import datetime, timezone

from src.models import ExchangeTypeEnum
from src.repositories import OrderRepository, OutboxEventRepository


def make_order_data(**overrides) -> dict:
    data = {
        "user_id": uuid.uuid4(),
        "products": {
            str(uuid.uuid4()): {"name": "apple", "price": 10.0, "quantity": 2}
        },
        "total_price": 20.0,
        "total_amount": 2,
    }
    data.update(overrides)
    return data


def make_outbox_data(**overrides) -> dict:
    data = {
        "exchange_name": "orders-events-exchange",
        "exchange_type": ExchangeTypeEnum.TOPIC,
        "routing_key": "order.created",
        "event_payload": {
            "event_id": str(uuid.uuid4()),
            "total_amount": 2,
            "total_price": 20.0,
            "products": [{"id": str(uuid.uuid4()), "quantity": 2}],
            "event_date": "2026-01-01",
            "user_email": "alice@example.com",
        },
    }
    data.update(overrides)
    return data


async def test_create_order_returns_persisted_entity(db_session) -> None:
    repo = OrderRepository(db_session)

    order = await repo.create_order(make_order_data())
    await db_session.commit()

    assert order is not None
    assert isinstance(order.id, uuid.UUID)
    assert order.total_price == 20.0
    assert order.created_at is not None
    assert order.products


async def test_get_order_by_id(db_session) -> None:
    repo = OrderRepository(db_session)
    created = await repo.create_order(make_order_data())
    await db_session.commit()

    order = await repo.get_order_by_id(created.id)

    assert order is not None
    assert order.id == created.id


async def test_get_order_by_id_returns_none_for_unknown_id(db_session) -> None:
    repo = OrderRepository(db_session)

    assert await repo.get_order_by_id(uuid.uuid4()) is None


async def test_get_orders_by_user_id(db_session) -> None:
    repo = OrderRepository(db_session)
    user_id = uuid.uuid4()
    await repo.create_order(make_order_data(user_id=user_id))
    await repo.create_order(make_order_data(user_id=user_id))
    await repo.create_order(make_order_data())
    await db_session.commit()

    orders = await repo.get_orders_by_user_id(user_id)

    assert len(orders) == 2
    assert all(order.user_id == user_id for order in orders)


async def test_create_outbox_event_returns_persisted_entity(db_session) -> None:
    repo = OutboxEventRepository(db_session)

    event = await repo.create_outbox_event(make_outbox_data())
    await db_session.commit()

    assert event is not None
    assert isinstance(event.id, uuid.UUID)
    assert event.exchange_type == ExchangeTypeEnum.TOPIC
    assert event.event_payload["total_amount"] == 2


async def test_get_last_outbox_events_orders_by_created_at(db_session) -> None:
    repo = OutboxEventRepository(db_session)
    later = await repo.create_outbox_event(
        make_outbox_data(created_at=datetime(2026, 1, 2, tzinfo=timezone.utc))
    )
    earlier = await repo.create_outbox_event(
        make_outbox_data(created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    )
    await db_session.commit()

    events = await repo.get_last_outbox_events(10)

    assert [event.id for event in events] == [earlier.id, later.id]


async def test_get_last_outbox_events_respects_limit(db_session) -> None:
    repo = OutboxEventRepository(db_session)
    for day in range(1, 4):
        await repo.create_outbox_event(
            make_outbox_data(created_at=datetime(2026, 1, day, tzinfo=timezone.utc))
        )
    await db_session.commit()

    events = await repo.get_last_outbox_events(2)

    assert len(events) == 2


async def test_delete_outbox_events(db_session) -> None:
    repo = OutboxEventRepository(db_session)
    first = await repo.create_outbox_event(make_outbox_data())
    second = await repo.create_outbox_event(make_outbox_data())
    await db_session.commit()

    await repo.delete_outbox_events([first.id])
    await db_session.commit()

    remaining = await repo.get_last_outbox_events(10)
    assert [event.id for event in remaining] == [second.id]


async def test_delete_outbox_events_with_empty_list_does_nothing(db_session) -> None:
    repo = OutboxEventRepository(db_session)
    event = await repo.create_outbox_event(make_outbox_data())
    await db_session.commit()

    await repo.delete_outbox_events([])
    await db_session.commit()

    remaining = await repo.get_last_outbox_events(10)
    assert [item.id for item in remaining] == [event.id]
