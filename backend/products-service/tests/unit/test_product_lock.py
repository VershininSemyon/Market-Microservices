
import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import fakeredis.aioredis
import pytest

import src.services as services_module
from src.exceptions import (
    DuplicateProductIdError,
    NotEnoughProductQuantityError,
    ProductNotFoundError,
)
from src.redis_cache_backend import get_lock_key
from src.redis_manager import redis_manager
from src.schemas import LockProductSchema
from src.services import ProductService


class FakeUnitOfWork:
    def __init__(self, product_repo: AsyncMock):
        self.product_repo = product_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def make_product(product_id: uuid.UUID, quantity: int) -> SimpleNamespace:
    return SimpleNamespace(id=product_id, quantity=quantity, is_active=True)


def lock_item(product_id: uuid.UUID, quantity: int) -> LockProductSchema:
    return LockProductSchema(product_id=product_id, quantity=quantity)


@pytest.fixture
async def fake_redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    redis_manager._client = client
    try:
        yield client
    finally:
        await client.flushall()
        await client.aclose()


@pytest.fixture
def product_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(product_repo: AsyncMock, fake_redis) -> ProductService:
    return ProductService(FakeUnitOfWork(product_repo))


async def test_lock_increments_and_accumulates(service, product_repo, fake_redis) -> None:
    product_id = uuid.uuid4()
    product_repo.get_active_products_by_ids.return_value = [make_product(product_id, 10)]

    await service.lock_products([lock_item(product_id, 2)])

    assert await fake_redis.get(get_lock_key(product_id)) == "2"

    await service.lock_products([lock_item(product_id, 3)])

    assert await fake_redis.get(get_lock_key(product_id)) == "5"


async def test_lock_raises_when_product_not_found_and_keeps_redis(service, product_repo, fake_redis) -> None:
    product_id = uuid.uuid4()
    await fake_redis.set(get_lock_key(product_id), 2)
    product_repo.get_active_products_by_ids.return_value = []

    with pytest.raises(ProductNotFoundError):
        await service.lock_products([lock_item(product_id, 1)])

    assert await fake_redis.get(get_lock_key(product_id)) == "2"


async def test_lock_raises_when_stock_is_not_enough_with_existing_lock(service, product_repo, fake_redis) -> None:
    product_id = uuid.uuid4()
    product_repo.get_active_products_by_ids.return_value = [make_product(product_id, 5)]
    await fake_redis.set(get_lock_key(product_id), 4)

    with pytest.raises(NotEnoughProductQuantityError):
        await service.lock_products([lock_item(product_id, 2)])

    assert await fake_redis.get(get_lock_key(product_id)) == "4"


async def test_lock_rolls_back_other_products_when_one_fails(service, product_repo, fake_redis) -> None:
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    product_repo.get_active_products_by_ids.return_value = [
        make_product(first_id, 10),
        make_product(second_id, 1),
    ]

    with pytest.raises(NotEnoughProductQuantityError):
        await service.lock_products([lock_item(first_id, 2), lock_item(second_id, 2)])

    assert int(await fake_redis.get(get_lock_key(first_id)) or 0) == 0
    assert int(await fake_redis.get(get_lock_key(second_id)) or 0) == 0


async def test_lock_rejects_duplicate_product_ids(service, product_repo, fake_redis) -> None:
    product_id = uuid.uuid4()

    with pytest.raises(DuplicateProductIdError):
        await service.lock_products([lock_item(product_id, 1), lock_item(product_id, 2)])

    product_repo.get_active_products_by_ids.assert_not_awaited()
    assert await fake_redis.get(get_lock_key(product_id)) is None


async def test_lock_propagates_redis_error_and_rolls_back(service, product_repo, fake_redis, monkeypatch) -> None:
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    product_repo.get_active_products_by_ids.return_value = [
        make_product(first_id, 10),
        make_product(second_id, 10),
    ]
    real_incrby = services_module.redis_cache.incrby

    async def fake_incrby(key: str, amount: int) -> int:
        if key == get_lock_key(second_id):
            raise RuntimeError("redis failed")
        return await real_incrby(key, amount)

    monkeypatch.setattr(services_module.redis_cache, "incrby", fake_incrby)

    with pytest.raises(RuntimeError, match="redis failed"):
        await service.lock_products([lock_item(first_id, 1), lock_item(second_id, 1)])

    assert int(await fake_redis.get(get_lock_key(first_id)) or 0) == 0


async def test_unlock_decreases_lock(service, product_repo, fake_redis) -> None:
    product_id = uuid.uuid4()
    await fake_redis.set(get_lock_key(product_id), 5)

    await service.unlock_products([lock_item(product_id, 2)])

    assert await fake_redis.get(get_lock_key(product_id)) == "3"


async def test_unlock_deletes_key_when_reaches_zero(service, product_repo, fake_redis) -> None:
    product_id = uuid.uuid4()
    await fake_redis.set(get_lock_key(product_id), 2)

    await service.unlock_products([lock_item(product_id, 2)])

    assert await fake_redis.get(get_lock_key(product_id)) is None


async def test_unlock_does_not_go_below_zero(service, product_repo, fake_redis) -> None:
    product_id = uuid.uuid4()
    await fake_redis.set(get_lock_key(product_id), 2)

    await service.unlock_products([lock_item(product_id, 5)])

    assert await fake_redis.get(get_lock_key(product_id)) is None


async def test_unlock_rejects_duplicate_product_ids(service, product_repo, fake_redis) -> None:
    product_id = uuid.uuid4()
    await fake_redis.set(get_lock_key(product_id), 5)

    with pytest.raises(DuplicateProductIdError):
        await service.unlock_products([lock_item(product_id, 1), lock_item(product_id, 2)])

    assert await fake_redis.get(get_lock_key(product_id)) == "5"


async def test_concurrent_locks_do_not_exceed_stock(service, product_repo, fake_redis) -> None:
    product_id = uuid.uuid4()
    product_repo.get_active_products_by_ids.return_value = [make_product(product_id, 3)]

    results = await asyncio.gather(
        *(
            service.lock_products([lock_item(product_id, 1)])
            for _ in range(10)
        ),
        return_exceptions=True,
    )

    successes = [result for result in results if result is None]
    failures = [result for result in results if isinstance(result, NotEnoughProductQuantityError)]

    assert len(successes) == 3
    assert len(failures) == 7
    assert await fake_redis.get(get_lock_key(product_id)) == "3"
