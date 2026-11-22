
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import src.services as services_module
from src.config import settings
from src.exceptions import (
    InvalidProductIdError,
    NotEnoughProductQuantityError,
    OrderNotFoundError,
    OrderOwnershipError,
)
from src.models import ExchangeTypeEnum
from src.schemas import OrderCreateSchema, OrderReadSchema
from src.services import OrderService


class FakeUnitOfWork:
    def __init__(self, order_repo: AsyncMock, outbox_repo: AsyncMock):
        self.order_repo = order_repo
        self.outbox_repo = outbox_repo
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def make_order(**overrides) -> SimpleNamespace:
    product_id = uuid.uuid4()
    data = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "products": {
            str(product_id): {"name": "apple", "price": 10.0, "quantity": 2}
        },
        "total_price": 20.0,
        "total_amount": 2,
        "created_at": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.fixture
def order_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def outbox_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(order_repo: AsyncMock, outbox_repo: AsyncMock) -> FakeUnitOfWork:
    return FakeUnitOfWork(order_repo, outbox_repo)


@pytest.fixture
def service(uow: FakeUnitOfWork) -> OrderService:
    return OrderService(uow)


@pytest.fixture(autouse=True)
def external(monkeypatch) -> SimpleNamespace:
    mocks = SimpleNamespace(get_product=AsyncMock())

    monkeypatch.setattr(services_module, "get_product", mocks.get_product)

    return mocks


async def test_get_user_orders(service, order_repo) -> None:
    user_id = uuid.uuid4()
    order_repo.get_orders_by_user_id.return_value = [make_order(user_id=user_id)]

    result = await service.get_user_orders(user_id)

    assert len(result) == 1
    assert isinstance(result[0], OrderReadSchema)
    order_repo.get_orders_by_user_id.assert_awaited_once_with(user_id)


async def test_get_user_orders_returns_empty_list(service, order_repo) -> None:
    order_repo.get_orders_by_user_id.return_value = []

    assert await service.get_user_orders(uuid.uuid4()) == []


async def test_get_order_by_id_success(service, order_repo) -> None:
    order = make_order()
    order_repo.get_order_by_id.return_value = order

    result = await service.get_order_by_id(order.user_id, order.id)

    assert result.id == order.id
    order_repo.get_order_by_id.assert_awaited_once_with(order.id)


async def test_get_order_by_id_raises_when_not_found(service, order_repo) -> None:
    order_repo.get_order_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await service.get_order_by_id(uuid.uuid4(), uuid.uuid4())


async def test_get_order_by_id_raises_when_not_owner(service, order_repo) -> None:
    order_repo.get_order_by_id.return_value = make_order()

    with pytest.raises(OrderOwnershipError):
        await service.get_order_by_id(uuid.uuid4(), uuid.uuid4())


async def test_create_order_success(service, uow, order_repo, outbox_repo, external) -> None:
    user_id = uuid.uuid4()
    first_product_id = uuid.uuid4()
    second_product_id = uuid.uuid4()
    data = OrderCreateSchema(
        products={first_product_id: 2, second_product_id: 1}
    )

    async def fake_get_product(product_id):
        return {
            "id": str(product_id),
            "name": f"name-{product_id}",
            "price": 10.0,
            "quantity": 5,
        }

    external.get_product.side_effect = fake_get_product
    order = make_order(
        user_id=user_id,
        products={
            str(first_product_id): {
                "name": f"name-{first_product_id}",
                "price": 10.0,
                "quantity": 2,
            },
            str(second_product_id): {
                "name": f"name-{second_product_id}",
                "price": 10.0,
                "quantity": 1,
            },
        },
        total_price=30.0,
        total_amount=3,
    )
    order_repo.create_order.return_value = order

    result = await service.create_order(user_id, "alice@example.com", data)

    assert result.id == order.id
    assert external.get_product.await_count == 2

    created_order = order_repo.create_order.call_args.args[0]
    assert created_order["user_id"] == user_id
    assert created_order["total_price"] == 30.0
    assert created_order["total_amount"] == 3
    assert created_order["products"] == {
        str(first_product_id): {
            "name": f"name-{first_product_id}",
            "price": 10.0,
            "quantity": 2,
        },
        str(second_product_id): {
            "name": f"name-{second_product_id}",
            "price": 10.0,
            "quantity": 1,
        },
    }

    outbox_data = outbox_repo.create_outbox_event.call_args.args[0]
    assert outbox_data["exchange_name"] == settings.ORDERS_EVENTS_EXCHANGE_NAME
    assert outbox_data["exchange_type"] == ExchangeTypeEnum.TOPIC
    assert outbox_data["routing_key"] == settings.ORDER_CREATED_ROUTING_KEY

    payload = outbox_data["event_payload"]
    assert uuid.UUID(payload["event_id"])
    assert payload["total_amount"] == 3
    assert payload["total_price"] == 30.0
    assert payload["user_email"] == "alice@example.com"
    assert payload["event_date"] == date.today().isoformat()
    assert {
        product["id"] for product in payload["products"]
    } == {str(first_product_id), str(second_product_id)}

    uow.commit.assert_awaited_once()


async def test_create_order_raises_when_not_enough_quantity(
    service,
    uow,
    order_repo,
    outbox_repo,
    external,
) -> None:
    product_id = uuid.uuid4()
    external.get_product.return_value = {
        "id": str(product_id),
        "name": "apple",
        "price": 10.0,
        "quantity": 1,
    }
    data = OrderCreateSchema(products={product_id: 2})

    with pytest.raises(NotEnoughProductQuantityError):
        await service.create_order(uuid.uuid4(), "alice@example.com", data)

    order_repo.create_order.assert_not_awaited()
    outbox_repo.create_outbox_event.assert_not_awaited()
    uow.commit.assert_not_awaited()


async def test_create_order_raises_when_product_not_found(
    service,
    uow,
    order_repo,
    outbox_repo,
    external,
) -> None:
    external.get_product.side_effect = InvalidProductIdError()
    data = OrderCreateSchema(products={uuid.uuid4(): 1})

    with pytest.raises(InvalidProductIdError):
        await service.create_order(uuid.uuid4(), "alice@example.com", data)

    order_repo.create_order.assert_not_awaited()
    outbox_repo.create_outbox_event.assert_not_awaited()
    uow.commit.assert_not_awaited()
