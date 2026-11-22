
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.consumer as consumer_module
from src.config import settings
from src.schemas import (
    OrderCreatedMessage,
    ProductCreatedMessage,
    ProductDeletedMessage,
    ReviewMessage,
    UserCreatedMessage,
    UserDeletedMessage,
)

SENDERS = [
    "send_welcome_email",
    "send_account_deleted_email",
    "send_product_created_email",
    "send_product_deleted_email",
    "send_review_created_email",
    "send_review_deleted_email",
    "send_order_created_email",
]


@pytest.fixture
def senders(monkeypatch) -> SimpleNamespace:
    mocks = SimpleNamespace(
        **{name: AsyncMock() for name in SENDERS}
    )
    for name in SENDERS:
        monkeypatch.setattr(consumer_module, name, getattr(mocks, name))
    return mocks


@pytest.fixture
def logger() -> MagicMock:
    return MagicMock()


@pytest.mark.parametrize(
    ("handler_name", "message", "sender_name", "expected_kwargs"),
    [
        (
            "process_user_created",
            UserCreatedMessage(username="alice", email="alice@example.com"),
            "send_welcome_email",
            {"username": "alice", "to_email": "alice@example.com"},
        ),
        (
            "process_user_deleted",
            UserDeletedMessage(email="alice@example.com"),
            "send_account_deleted_email",
            {"to_email": "alice@example.com"},
        ),
        (
            "process_product_created",
            ProductCreatedMessage(
                product_name="apple",
                created_by="alice@example.com",
            ),
            "send_product_created_email",
            {"product_name": "apple", "to_email": "alice@example.com"},
        ),
        (
            "process_product_deleted",
            ProductDeletedMessage(
                product_name="apple",
                deleted_by="alice@example.com",
            ),
            "send_product_deleted_email",
            {"product_name": "apple", "to_email": "alice@example.com"},
        ),
        (
            "process_review_created",
            ReviewMessage(product_id="product-1", user_email="alice@example.com"),
            "send_review_created_email",
            {"product_id": "product-1", "to_email": "alice@example.com"},
        ),
        (
            "process_review_deleted",
            ReviewMessage(product_id="product-1", user_email="alice@example.com"),
            "send_review_deleted_email",
            {"product_id": "product-1", "to_email": "alice@example.com"},
        ),
        (
            "process_order_created",
            OrderCreatedMessage(
                total_price=20.5,
                total_amount=2,
                user_email="alice@example.com",
            ),
            "send_order_created_email",
            {
                "total_price": 20.5,
                "total_amount": 2,
                "to_email": "alice@example.com",
            },
        ),
    ],
)
async def test_handler_sends_email(
    senders: SimpleNamespace,
    logger: MagicMock,
    handler_name: str,
    message,
    sender_name: str,
    expected_kwargs: dict,
) -> None:
    handler = getattr(consumer_module, handler_name)

    await handler(message, logger)

    sender = getattr(senders, sender_name)
    sender.assert_awaited_once_with(**expected_kwargs)
    logger.info.assert_called_once()


async def test_handler_does_not_call_other_senders(
    senders: SimpleNamespace,
    logger: MagicMock,
) -> None:
    await consumer_module.process_user_created(
        UserCreatedMessage(username="alice", email="alice@example.com"),
        logger,
    )

    assert senders.send_welcome_email.await_count == 1
    for name in SENDERS:
        if name != "send_welcome_email":
            getattr(senders, name).assert_not_awaited()


async def test_handler_propagates_sender_error(
    senders: SimpleNamespace,
    logger: MagicMock,
) -> None:
    senders.send_welcome_email.side_effect = RuntimeError("smtp is down")

    with pytest.raises(RuntimeError):
        await consumer_module.process_user_created(
            UserCreatedMessage(username="alice", email="alice@example.com"),
            logger,
        )


async def test_handle_dlq_logs_exchange_and_body(logger: MagicMock) -> None:
    message = SimpleNamespace(
        headers={"x-first-death-exchange": "user-events-exchange"}
    )

    await consumer_module.handle_dlq({"email": "alice@example.com"}, logger, message)

    logger.error.assert_called_once()
    logged = logger.error.call_args.args[0]
    assert "user-events-exchange" in logged
    assert "alice@example.com" in logged


async def test_handle_dlq_without_death_header(logger: MagicMock) -> None:
    message = SimpleNamespace(headers={})

    await consumer_module.handle_dlq({}, logger, message)

    logger.error.assert_called_once()


def test_create_queue_builds_durable_queue_with_dlq() -> None:
    queue = consumer_module.create_queue("test-queue", "test.key")

    assert queue.name == "test-queue"
    assert queue.routing_key == "test.key"
    assert queue.durable is True
    assert queue.arguments["x-dead-letter-exchange"] == settings.DLX_EXCHANGE_NAME


def test_exchanges_are_declared_as_durable_topics() -> None:
    assert consumer_module.user_exchange.name == settings.USER_EVENTS_EXCHANGE_NAME
    assert consumer_module.products_exchange.name == settings.PRODUCTS_EVENTS_EXCHANGE_NAME
    assert consumer_module.reviews_exchange.name == settings.REVIEWS_EVENTS_EXCHANGE_NAME
    assert consumer_module.order_exchange.name == settings.ORDERS_EVENTS_EXCHANGE_NAME
    assert consumer_module.dlx_exchange.name == settings.DLX_EXCHANGE_NAME

    for exchange in (
        consumer_module.user_exchange,
        consumer_module.products_exchange,
        consumer_module.reviews_exchange,
        consumer_module.order_exchange,
        consumer_module.dlx_exchange,
    ):
        assert exchange.type == "topic"
        assert exchange.durable is True


def test_dlq_is_declared_as_durable_catch_all() -> None:
    assert consumer_module.dlq.name == settings.DLQ_NAME
    assert consumer_module.dlq.durable is True
    assert consumer_module.dlq.routing_key == "#"
