
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import aio_pika
import pytest

import src.consumer as consumer_module
from src.config import settings
from src.consumer import RabbitMQConsumer


@pytest.fixture
def consumer() -> RabbitMQConsumer:
    return RabbitMQConsumer(amqp_url="amqp://test")


@pytest.fixture
def redis(monkeypatch) -> SimpleNamespace:
    fake = SimpleNamespace(connect=AsyncMock(), disconnect=AsyncMock())
    monkeypatch.setattr(consumer_module, "redis_manager", fake)
    return fake


@pytest.fixture
def cache(monkeypatch) -> AsyncMock:
    fake = AsyncMock()
    monkeypatch.setattr(consumer_module, "redis_cache", fake)
    return fake


def make_message(payload, headers: dict | None = None):
    if isinstance(payload, bytes):
        body = payload
    else:
        body = json.dumps(payload).encode("utf-8")

    message = AsyncMock()
    message.body = body
    message.headers = headers or {}
    message.ack = AsyncMock()
    message.nack = AsyncMock()
    return message


async def test_connect_creates_connection_and_connects_redis(monkeypatch, consumer, redis) -> None:
    connection = MagicMock()
    connection.is_closed = False
    connection.channel = AsyncMock()
    connect_robust = AsyncMock(return_value=connection)
    monkeypatch.setattr(consumer_module.aio_pika, "connect_robust", connect_robust)

    await consumer.connect()

    connect_robust.assert_awaited_once_with("amqp://test")
    connection.channel.assert_awaited_once()
    redis.connect.assert_awaited_once()


async def test_connect_reuses_open_connection(monkeypatch, consumer, redis) -> None:
    connection = MagicMock()
    connection.is_closed = False
    connection.channel = AsyncMock()
    connect_robust = AsyncMock(return_value=connection)
    monkeypatch.setattr(consumer_module.aio_pika, "connect_robust", connect_robust)

    await consumer.connect()
    await consumer.connect()

    connect_robust.assert_awaited_once()
    assert redis.connect.await_count == 2


async def test_close_closes_resources_and_disconnects_redis(consumer, redis) -> None:
    connection = MagicMock()
    connection.is_closed = False
    connection.close = AsyncMock()
    channel = MagicMock()
    channel.is_closed = False
    channel.close = AsyncMock()
    consumer._connection = connection
    consumer._channel = channel

    await consumer.close()

    channel.close.assert_awaited_once()
    connection.close.assert_awaited_once()
    redis.disconnect.assert_awaited_once()


async def test_close_skips_closed_resources(consumer, redis) -> None:
    connection = MagicMock()
    connection.is_closed = True
    connection.close = AsyncMock()
    channel = MagicMock()
    channel.is_closed = True
    channel.close = AsyncMock()
    consumer._connection = connection
    consumer._channel = channel

    await consumer.close()

    channel.close.assert_not_awaited()
    connection.close.assert_not_awaited()
    redis.disconnect.assert_awaited_once()


async def test_process_order_created_updates_products_and_acks(consumer, cache) -> None:
    consumer._update_product_data = AsyncMock()
    message = make_message(
        {
            "event_id": "event-1",
            "products": [
                {"id": "product-1", "quantity": 2},
                {"id": "product-2", "quantity": 3},
            ],
        }
    )

    await consumer.process_order_created(message)

    cache.get_value.assert_awaited_once_with("events:event-1")
    assert consumer._update_product_data.await_count == 2
    consumer._update_product_data.assert_any_await("product-1", 2)
    consumer._update_product_data.assert_any_await("product-2", 3)
    cache.set_value.assert_awaited_once_with("events:event-1", "done", 3600 * 24 * 3)
    message.ack.assert_awaited_once()
    message.nack.assert_not_awaited()


async def test_process_order_created_skips_already_processed_event(consumer, cache) -> None:
    consumer._update_product_data = AsyncMock()
    cache.get_value.return_value = "done"
    message = make_message(
        {"event_id": "event-1", "products": [{"id": "product-1", "quantity": 1}]}
    )

    await consumer.process_order_created(message)

    message.ack.assert_awaited_once()
    message.nack.assert_not_awaited()
    consumer._update_product_data.assert_not_awaited()
    cache.set_value.assert_not_awaited()


async def test_process_order_created_nacks_message_without_event_id(consumer, cache) -> None:
    message = make_message({"products": [{"id": "product-1", "quantity": 1}]})

    await consumer.process_order_created(message)

    message.nack.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()
    cache.get_value.assert_not_awaited()


async def test_process_order_created_nacks_message_without_products(consumer, cache) -> None:
    message = make_message({"event_id": "event-1"})

    await consumer.process_order_created(message)

    message.nack.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()


async def test_process_order_created_nacks_invalid_product(consumer, cache) -> None:
    message = make_message(
        {"event_id": "event-1", "products": [{"id": "product-1"}]}
    )

    await consumer.process_order_created(message)

    message.nack.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()


async def test_process_order_created_nacks_invalid_json(consumer, cache) -> None:
    message = make_message(b"not-json")

    await consumer.process_order_created(message)

    message.nack.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()
    cache.get_value.assert_not_awaited()


async def test_process_order_created_nacks_on_unexpected_error(consumer, cache) -> None:
    consumer._update_product_data = AsyncMock(side_effect=RuntimeError("boom"))
    message = make_message(
        {"event_id": "event-1", "products": [{"id": "product-1", "quantity": 1}]}
    )

    await consumer.process_order_created(message)

    message.nack.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()
    cache.set_value.assert_not_awaited()


async def test_process_dlq_acks_json_message(consumer) -> None:
    message = make_message(
        {"event": "payload"},
        headers={"x-first-death-exchange": "orders", "x-first-death-queue": "queue"},
    )

    await consumer.process_dlq(message)

    message.ack.assert_awaited_once()
    message.nack.assert_not_awaited()


async def test_process_dlq_acks_non_json_message(consumer) -> None:
    message = make_message(b"plain text")

    await consumer.process_dlq(message)

    message.ack.assert_awaited_once()
    message.nack.assert_not_awaited()


async def test_process_dlq_nacks_on_unexpected_error(consumer) -> None:
    message = AsyncMock()
    message.body = None
    message.headers = {}
    message.ack = AsyncMock()
    message.nack = AsyncMock()

    await consumer.process_dlq(message)

    message.nack.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()


async def test_start_consuming_declares_topology(consumer) -> None:
    consumer.connect = AsyncMock()
    order_exchange = MagicMock()
    dlx = MagicMock()
    order_queue = MagicMock()
    order_queue.bind = AsyncMock()
    order_queue.consume = AsyncMock()
    dlq = MagicMock()
    dlq.bind = AsyncMock()
    dlq.consume = AsyncMock()

    channel = MagicMock()
    channel.declare_exchange = AsyncMock(side_effect=[order_exchange, dlx])
    channel.declare_queue = AsyncMock(side_effect=[order_queue, dlq])
    consumer._channel = channel

    await consumer.start_consuming()

    consumer.connect.assert_awaited_once()

    assert channel.declare_exchange.await_count == 2
    channel.declare_exchange.assert_any_await(
        name=settings.ORDERS_EVENTS_EXCHANGE_NAME,
        type=aio_pika.ExchangeType.TOPIC,
        durable=True,
    )
    channel.declare_exchange.assert_any_await(
        name=settings.DLX_EXCHANGE_NAME,
        type=aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    channel.declare_queue.assert_any_await(
        name=settings.ORDER_CREATED_QUEUE_NAME,
        durable=True,
        arguments={"x-dead-letter-exchange": settings.DLX_EXCHANGE_NAME},
    )
    channel.declare_queue.assert_any_await(
        name=settings.DLQ_NAME,
        durable=True,
    )

    order_queue.bind.assert_awaited_once_with(
        exchange=order_exchange,
        routing_key=settings.ORDER_CREATED_ROUTING_KEY,
    )
    dlq.bind.assert_awaited_once_with(exchange=dlx, routing_key="#")

    order_queue.consume.assert_awaited_once_with(consumer.process_order_created)
    dlq.consume.assert_awaited_once_with(consumer.process_dlq)
