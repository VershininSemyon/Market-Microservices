
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.consumer as consumer_module
from src.config import settings
from src.enums import EntityTypeEnum, EventTypeEnum
from src.schemas import EventDateMessageSchema
from src.services import AnalyticsService
from src.unitofwork import UnitOfWork


@pytest.fixture
def service(monkeypatch) -> SimpleNamespace:
    fake_service = SimpleNamespace(add_analytics=AsyncMock())
    monkeypatch.setattr(
        consumer_module,
        "create_analytics_service",
        MagicMock(return_value=fake_service),
    )
    return fake_service


@pytest.fixture
def logger() -> MagicMock:
    return MagicMock()


@pytest.mark.parametrize(
    ("handler_name", "entity_type", "event_type"),
    [
        ("process_user_created", EntityTypeEnum.USER, EventTypeEnum.CREATED),
        ("process_user_deleted", EntityTypeEnum.USER, EventTypeEnum.DELETED),
        ("process_product_created", EntityTypeEnum.PRODUCT, EventTypeEnum.CREATED),
        ("process_product_deleted", EntityTypeEnum.PRODUCT, EventTypeEnum.DELETED),
        ("process_review_created", EntityTypeEnum.REVIEW, EventTypeEnum.CREATED),
        ("process_review_deleted", EntityTypeEnum.REVIEW, EventTypeEnum.DELETED),
        ("process_order_created", EntityTypeEnum.ORDER, EventTypeEnum.CREATED),
    ],
)
async def test_handler_adds_analytics(
    handler_name: str,
    entity_type: EntityTypeEnum,
    event_type: EventTypeEnum,
    service: SimpleNamespace,
    logger: MagicMock,
) -> None:
    handler = getattr(consumer_module, handler_name)
    msg = EventDateMessageSchema(event_date=date(2026, 2, 3))

    await handler(msg, logger)

    service.add_analytics.assert_awaited_once_with(
        entity_type=entity_type,
        event_type=event_type,
        day=date(2026, 2, 3),
    )


async def test_handler_logs_event(service: SimpleNamespace, logger: MagicMock) -> None:
    await consumer_module.process_order_created(
        EventDateMessageSchema(event_date=date(2026, 2, 3)),
        logger,
    )

    logger.info.assert_called_once()


async def test_handle_dlq_logs_exchange_and_body(logger: MagicMock) -> None:
    message = SimpleNamespace(
        headers={"x-first-death-exchange": "products-events-exchange"}
    )

    await consumer_module.handle_dlq({"event_date": "2026-02-03"}, logger, message)

    logger.error.assert_called_once()
    logged = logger.error.call_args.args[0]
    assert "products-events-exchange" in logged
    assert "2026-02-03" in logged


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


def test_create_analytics_service_builds_service_with_uow() -> None:
    service = consumer_module.create_analytics_service()

    assert isinstance(service, AnalyticsService)
    assert isinstance(service.uow, UnitOfWork)
    assert service.uow.session_factory is consumer_module.async_session_factory


def test_exchanges_are_declared_as_durable_topics() -> None:
    assert consumer_module.user_exchange.name == settings.USER_EVENTS_EXCHANGE_NAME
    assert consumer_module.products_exchange.name == settings.PRODUCTS_EVENTS_EXCHANGE_NAME
    assert consumer_module.reviews_exchange.name == settings.REVIEWS_EVENTS_EXCHANGE_NAME
    assert consumer_module.orders_exchange.name == settings.ORDERS_EVENTS_EXCHANGE_NAME
    assert consumer_module.dlx_exchange.name == settings.DLX_EXCHANGE_NAME

    for exchange in (
        consumer_module.user_exchange,
        consumer_module.products_exchange,
        consumer_module.reviews_exchange,
        consumer_module.orders_exchange,
        consumer_module.dlx_exchange,
    ):
        assert exchange.type == "topic"
        assert exchange.durable is True


def test_dlq_is_declared_as_durable_catch_all() -> None:
    assert consumer_module.dlq.name == settings.DLQ_NAME
    assert consumer_module.dlq.durable is True
    assert consumer_module.dlq.routing_key == "#"
