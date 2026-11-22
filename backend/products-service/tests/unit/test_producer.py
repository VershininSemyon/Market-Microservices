
import json
from unittest.mock import AsyncMock, MagicMock

import aio_pika
import pytest

import src.producer as producer_module
from src.config import settings
from src.producer import RabbitMQProducer


@pytest.fixture
def broker():
    connection = MagicMock()
    connection.is_closed = False
    connection.close = AsyncMock()

    channel = MagicMock()
    channel.is_closed = False
    channel.close = AsyncMock()

    exchange = MagicMock()
    exchange.publish = AsyncMock()

    channel.declare_exchange = AsyncMock(return_value=exchange)
    connection.channel = AsyncMock(return_value=channel)

    return connection, channel, exchange


async def test_connect_creates_connection_and_channel(monkeypatch, broker) -> None:
    connection, channel, _ = broker
    connect_robust = AsyncMock(return_value=connection)
    monkeypatch.setattr(producer_module.aio_pika, "connect_robust", connect_robust)

    producer = RabbitMQProducer(amqp_url="amqp://test")

    await producer.connect()

    connect_robust.assert_awaited_once_with("amqp://test")
    connection.channel.assert_awaited_once()
    assert producer._connection is connection
    assert producer._channel is channel


async def test_connect_does_not_recreate_open_connection(monkeypatch, broker) -> None:
    connection, _, _ = broker
    connect_robust = AsyncMock(return_value=connection)
    monkeypatch.setattr(producer_module.aio_pika, "connect_robust", connect_robust)

    producer = RabbitMQProducer(amqp_url="amqp://test")

    await producer.connect()
    await producer.connect()

    connect_robust.assert_awaited_once()


async def test_close_closes_channel_and_connection(broker) -> None:
    connection, channel, _ = broker

    producer = RabbitMQProducer(amqp_url="amqp://test")
    producer._connection = connection
    producer._channel = channel

    await producer.close()

    channel.close.assert_awaited_once()
    connection.close.assert_awaited_once()


async def test_close_skips_already_closed_resources(broker) -> None:
    connection, channel, _ = broker
    connection.is_closed = True
    channel.is_closed = True

    producer = RabbitMQProducer(amqp_url="amqp://test")
    producer._connection = connection
    producer._channel = channel

    await producer.close()

    channel.close.assert_not_awaited()
    connection.close.assert_not_awaited()


async def test_publish_message_declares_exchange_and_publishes_json(monkeypatch, broker) -> None:
    connection, channel, exchange = broker
    connect_robust = AsyncMock(return_value=connection)
    monkeypatch.setattr(producer_module.aio_pika, "connect_robust", connect_robust)

    producer = RabbitMQProducer(amqp_url="amqp://test")

    await producer.publish_message(
        routing_key=settings.PRODUCT_CREATED_ROUTING_KEY,
        message_body={"product_name": "apple"},
    )

    channel.declare_exchange.assert_awaited_once_with(
        name=settings.PRODUCTS_EVENTS_EXCHANGE_NAME,
        type=aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    exchange.publish.assert_awaited_once()
    publish_kwargs = exchange.publish.call_args.kwargs
    assert publish_kwargs["routing_key"] == settings.PRODUCT_CREATED_ROUTING_KEY

    message = publish_kwargs["message"]
    assert json.loads(message.body) == {"product_name": "apple"}
    assert message.content_type == "application/json"
    assert message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
