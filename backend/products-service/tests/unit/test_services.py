
import json
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, call

import pytest

import src.services as services_module
from src.config import settings
from src.enums import ProductSortFieldEnum, SortOrderEnum
from src.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from src.schemas import (
    ProductCreateSchema,
    ProductQueryParams,
    ProductReadSchema,
    ProductUpdateSchema,
)
from src.services import ProductService


class FakeUnitOfWork:
    def __init__(self, product_repo: AsyncMock):
        self.product_repo = product_repo
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def make_product(**overrides) -> SimpleNamespace:
    data = {
        "id": uuid.uuid4(),
        "name": "apple",
        "description": "green apple",
        "price": 10.0,
        "quantity": 5,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.fixture
def product_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(product_repo: AsyncMock) -> FakeUnitOfWork:
    return FakeUnitOfWork(product_repo)


@pytest.fixture
def service(uow: FakeUnitOfWork) -> ProductService:
    return ProductService(uow)


@pytest.fixture(autouse=True)
def external(monkeypatch) -> SimpleNamespace:
    mocks = SimpleNamespace(
        redis_cache=SimpleNamespace(
            set_value=AsyncMock(),
            get_value=AsyncMock(),
            del_key=AsyncMock(),
        ),
        rabbitmq_producer=SimpleNamespace(publish_message=AsyncMock()),
        index_product=AsyncMock(),
        delete_product_index=AsyncMock(),
        search_product=AsyncMock(return_value=[]),
    )

    monkeypatch.setattr(services_module, "redis_cache", mocks.redis_cache)
    monkeypatch.setattr(services_module, "rabbitmq_producer", mocks.rabbitmq_producer)
    monkeypatch.setattr(services_module, "index_product", mocks.index_product)
    monkeypatch.setattr(services_module, "delete_product_index", mocks.delete_product_index)
    monkeypatch.setattr(services_module, "search_product", mocks.search_product)

    return mocks


async def test_invalidate_products_cache_without_product(service, external) -> None:
    await service.invalidate_products_cache()

    external.redis_cache.del_key.assert_awaited_once_with("products:list")


async def test_invalidate_products_cache_with_product(service, external) -> None:
    product_id = uuid.uuid4()

    await service.invalidate_products_cache(product_id)

    external.redis_cache.del_key.assert_has_awaits(
        [call("products:list"), call(f"products:{product_id}")]
    )


async def test_create_product_success(service, uow, product_repo, external) -> None:
    product = make_product()
    product_repo.get_product_by_name.return_value = None
    product_repo.create_product.return_value = product
    data = ProductCreateSchema(
        name="apple",
        description="green apple",
        price=10.0,
        quantity=5,
    )

    result = await service.create_product(data, "admin@example.com")

    assert isinstance(result, ProductReadSchema)
    assert result.id == product.id
    product_repo.create_product.assert_awaited_once_with(data.model_dump())
    uow.commit.assert_awaited_once()
    external.redis_cache.del_key.assert_awaited_once_with("products:list")
    external.index_product.assert_awaited_once_with(product.id, "apple", "green apple")
    external.rabbitmq_producer.publish_message.assert_awaited_once_with(
        routing_key=settings.PRODUCT_CREATED_ROUTING_KEY,
        message_body={
            "product_name": "apple",
            "created_by": "admin@example.com",
            "event_date": date.today().isoformat(),
        },
    )


async def test_create_product_raises_when_name_exists(service, uow, product_repo, external) -> None:
    product_repo.get_product_by_name.return_value = make_product()
    data = ProductCreateSchema(name="apple", price=10.0, quantity=5)

    with pytest.raises(ProductAlreadyExistsError):
        await service.create_product(data, "admin@example.com")

    product_repo.create_product.assert_not_awaited()
    uow.commit.assert_not_awaited()
    external.rabbitmq_producer.publish_message.assert_not_awaited()


async def test_get_products_list_returns_cached_default_page(service, product_repo, external) -> None:
    product = make_product()
    cached = [ProductReadSchema.model_validate(product).model_dump(mode="json")]
    external.redis_cache.get_value.return_value = json.dumps(cached)

    result = await service.get_products_list(ProductQueryParams())

    assert len(result) == 1
    assert result[0].id == product.id
    product_repo.list_products.assert_not_awaited()
    external.redis_cache.set_value.assert_not_awaited()


async def test_get_products_list_caches_default_page_on_miss(service, product_repo, external) -> None:
    product = make_product()
    external.redis_cache.get_value.return_value = None
    product_repo.list_products.return_value = [product]

    result = await service.get_products_list(ProductQueryParams())

    assert len(result) == 1
    product_repo.list_products.assert_awaited_once_with()
    external.redis_cache.set_value.assert_awaited_once()
    key, value, ttl = external.redis_cache.set_value.call_args.args
    assert key == "products:list"
    assert ttl == 3600 * 24
    assert json.loads(value)[0]["id"] == str(product.id)


async def test_get_products_list_uses_search_for_text_query(service, product_repo, external) -> None:
    product = make_product()
    external.search_product.return_value = ["product-1"]
    product_repo.list_products.return_value = [product]
    filters = ProductQueryParams(
        text_query="apple",
        min_price=1.0,
        max_price=10.0,
        order_by=ProductSortFieldEnum.PRICE,
        order=SortOrderEnum.DESC,
        limit=5,
        offset=2,
    )

    result = await service.get_products_list(filters)

    assert len(result) == 1
    external.search_product.assert_awaited_once_with("apple", 5)
    product_repo.list_products.assert_awaited_once_with(
        product_ids=["product-1"],
        min_price=1.0,
        max_price=10.0,
        order_by=ProductSortFieldEnum.PRICE,
        order=SortOrderEnum.DESC,
        limit=5,
        offset=2,
    )


async def test_get_products_list_skips_search_without_text_query(service, product_repo, external) -> None:
    product = make_product()
    product_repo.list_products.return_value = [product]
    filters = ProductQueryParams(min_price=1.0)

    await service.get_products_list(filters)

    external.search_product.assert_not_awaited()
    product_repo.list_products.assert_awaited_once_with(
        product_ids=None,
        min_price=1.0,
        max_price=None,
        order_by=None,
        order=SortOrderEnum.ASC,
        limit=10,
        offset=0,
    )


async def test_delete_product_success(service, uow, product_repo, external) -> None:
    product = make_product()
    product_repo.get_product_by_id.return_value = product

    await service.delete_product(product.id, "admin@example.com")

    product_repo.delete_product.assert_awaited_once_with(product.id)
    uow.commit.assert_awaited_once()
    external.redis_cache.del_key.assert_has_awaits(
        [call("products:list"), call(f"products:{product.id}")]
    )
    external.delete_product_index.assert_awaited_once_with(product.id)
    external.rabbitmq_producer.publish_message.assert_awaited_once_with(
        routing_key=settings.PRODUCT_DELETED_ROUTING_KEY,
        message_body={
            "product_id": str(product.id),
            "product_name": "apple",
            "deleted_by": "admin@example.com",
            "event_date": date.today().isoformat(),
        },
    )


async def test_delete_product_raises_when_not_found(service, uow, product_repo, external) -> None:
    product_repo.get_product_by_id.return_value = None

    with pytest.raises(ProductNotFoundError):
        await service.delete_product(uuid.uuid4(), "admin@example.com")

    product_repo.delete_product.assert_not_awaited()
    uow.commit.assert_not_awaited()
    external.rabbitmq_producer.publish_message.assert_not_awaited()


async def test_get_product_by_id_returns_cached_product(service, product_repo, external) -> None:
    product = make_product()
    external.redis_cache.get_value.return_value = ProductReadSchema.model_validate(product).model_dump_json()

    result = await service.get_product_by_id(product.id)

    assert result.id == product.id
    product_repo.get_product_by_id.assert_not_awaited()


async def test_get_product_by_id_caches_product_on_miss(service, product_repo, external) -> None:
    product = make_product()
    external.redis_cache.get_value.return_value = None
    product_repo.get_product_by_id.return_value = product

    result = await service.get_product_by_id(product.id)

    assert result.id == product.id
    external.redis_cache.set_value.assert_awaited_once()
    key, value, ttl = external.redis_cache.set_value.call_args.args
    assert key == f"products:{product.id}"
    assert ttl == 3600 * 24 * 7
    assert json.loads(value)["id"] == str(product.id)


async def test_get_product_by_id_raises_when_not_found(service, product_repo, external) -> None:
    external.redis_cache.get_value.return_value = None
    product_repo.get_product_by_id.return_value = None

    with pytest.raises(ProductNotFoundError):
        await service.get_product_by_id(uuid.uuid4())

    external.redis_cache.set_value.assert_not_awaited()


async def test_update_product_success(service, uow, product_repo, external) -> None:
    product = make_product(description="red apple", price=12.0, quantity=3)
    product_repo.get_product_by_name.return_value = make_product(id=product.id)
    product_repo.update_product.return_value = product
    data = ProductUpdateSchema(
        name="apple",
        description="red apple",
        price=12.0,
        quantity=3,
    )

    result = await service.update_product(product.id, data)

    assert result.id == product.id
    product_repo.update_product.assert_awaited_once_with(product.id, data.model_dump())
    uow.commit.assert_awaited_once()
    external.redis_cache.del_key.assert_has_awaits(
        [call("products:list"), call(f"products:{product.id}")]
    )
    external.index_product.assert_awaited_once_with(product.id, "apple", "red apple")


async def test_update_product_raises_when_name_belongs_to_other_product(service, product_repo, external) -> None:
    product_repo.get_product_by_name.return_value = make_product(id=uuid.uuid4())
    data = ProductUpdateSchema(name="apple", description=None, price=12.0, quantity=3)

    with pytest.raises(ProductAlreadyExistsError):
        await service.update_product(uuid.uuid4(), data)

    product_repo.update_product.assert_not_awaited()
    external.index_product.assert_not_awaited()


async def test_update_product_raises_when_not_found(service, product_repo, external) -> None:
    product_repo.get_product_by_name.return_value = None
    product_repo.update_product.return_value = None
    data = ProductUpdateSchema(name="apple", description=None, price=12.0, quantity=3)

    with pytest.raises(ProductNotFoundError):
        await service.update_product(uuid.uuid4(), data)

    external.index_product.assert_not_awaited()
