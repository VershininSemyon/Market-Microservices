
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import aio_pika
import pytest

import src.consumer as consumer_module
from src.config import settings
from src.consumer import RabbitMQConsumer


class FakeUnitOfWork:
    def __init__(self, repo: AsyncMock):
        self.review_repo = repo
        self.commit = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


@pytest.fixture
def consumer() -> RabbitMQConsumer:
    return RabbitMQConsumer(amqp_url="amqp://test")


@pytest.fixture
def redis(monkeypatch) -> SimpleNamespace:
    fake = SimpleNamespace(connect=AsyncMock(), disconnect=AsyncMock())
    monkeypatch.setattr(consumer_module, "redis_manager", fake)
    return fake


@pytest.fixture
def review_dependencies(monkeypatch) -> SimpleNamespace:
    repo = AsyncMock()
    uow = FakeUnitOfWork(repo)
    uow_factory = MagicMock(return_value=uow)
    service = SimpleNamespace(invalidate_review_list_cache=AsyncMock())
    service_factory = MagicMock(return_value=service)

    monkeypatch.setattr(consumer_module, "UnitOfWork", uow_factory)
    monkeypatch.setattr(consumer_module, "ReviewService", service_factory)

    return SimpleNamespace(
        repo=repo,
        uow=uow,
        uow_factory=uow_factory,
        service=service,
        service_factory=service_factory,
    )


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


async def test_process_product_deleted_removes_reviews_and_acks(consumer, review_dependencies) -> None:
    message = make_message({"product_id": "product-1"})

    await consumer.process_product_deleted(message)

    review_dependencies.uow_factory.assert_called_once()
    review_dependencies.repo.delete_product_reviews.assert_awaited_once_with("product-1")
    review_dependencies.uow.commit.assert_awaited_once()
    review_dependencies.service.invalidate_review_list_cache.assert_awaited_once_with("product-1")
    message.ack.assert_awaited_once()
    message.nack.assert_not_awaited()


async def test_process_product_deleted_nacks_message_without_product_id(
    consumer,
    review_dependencies,
) -> None:
    message = make_message({})

    await consumer.process_product_deleted(message)

    message.nack.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()
    review_dependencies.uow_factory.assert_not_called()


async def test_process_product_deleted_nacks_invalid_json(consumer, review_dependencies) -> None:
    message = make_message(b"not-json")

    await consumer.process_product_deleted(message)

    message.nack.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()
    review_dependencies.uow_factory.assert_not_called()


async def test_process_product_deleted_nacks_on_unexpected_error(
    consumer,
    review_dependencies,
) -> None:
    review_dependencies.repo.delete_product_reviews.side_effect = RuntimeError("boom")
    message = make_message({"product_id": "product-1"})

    await consumer.process_product_deleted(message)

    message.nack.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()


async def test_process_dlq_acks_json_message(consumer) -> None:
    message = make_message(
        {"event": "payload"},
        headers={"x-first-death-exchange": "products", "x-first-death-queue": "queue"},
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
    product_exchange = MagicMock()
    dlx = MagicMock()
    product_queue = MagicMock()
    product_queue.bind = AsyncMock()
    product_queue.consume = AsyncMock()
    dlq = MagicMock()
    dlq.bind = AsyncMock()
    dlq.consume = AsyncMock()

    channel = MagicMock()
    channel.declare_exchange = AsyncMock(side_effect=[product_exchange, dlx])
    channel.declare_queue = AsyncMock(side_effect=[product_queue, dlq])
    consumer._channel = channel

    await consumer.start_consuming()

    consumer.connect.assert_awaited_once()

    assert channel.declare_exchange.await_count == 2
    channel.declare_exchange.assert_any_await(
        name=settings.PRODUCTS_EVENTS_EXCHANGE_NAME,
        type=aio_pika.ExchangeType.TOPIC,
        durable=True,
    )
    channel.declare_exchange.assert_any_await(
        name=settings.DLX_EXCHANGE_NAME,
        type=aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    channel.declare_queue.assert_any_await(
        name=settings.PRODUCT_DELETED_QUEUE_NAME,
        durable=True,
        arguments={"x-dead-letter-exchange": settings.DLX_EXCHANGE_NAME},
    )
    channel.declare_queue.assert_any_await(
        name=settings.DLQ_NAME,
        durable=True,
    )

    product_queue.bind.assert_awaited_once_with(
        exchange=product_exchange,
        routing_key=settings.PRODUCT_DELETED_ROUTING_KEY,
    )
    dlq.bind.assert_awaited_once_with(exchange=dlx, routing_key="#")

    product_queue.consume.assert_awaited_once_with(consumer.process_product_deleted)
    dlq.consume.assert_awaited_once_with(consumer.process_dlq)
