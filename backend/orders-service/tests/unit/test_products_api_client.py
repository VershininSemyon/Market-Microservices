
import json
import uuid
from unittest.mock import AsyncMock

import httpx
import pytest

import src.products_api_client as client_module
from src.config import settings
from src.exceptions import InvalidProductIdError, NotEnoughProductQuantityError
from src.products_api_client import get_product, lock_products, unlock_products

REAL_ASYNC_CLIENT = httpx.AsyncClient


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch) -> AsyncMock:
    sleep = AsyncMock()
    monkeypatch.setattr(client_module.asyncio, "sleep", sleep)
    return sleep


def install_transport(monkeypatch, handler) -> None:
    def factory(*args, **kwargs):
        return REAL_ASYNC_CLIENT(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(client_module.httpx, "AsyncClient", factory)


async def test_get_product_returns_data(monkeypatch) -> None:
    calls = []
    product = {"id": "product-1", "name": "apple", "price": 10.0, "quantity": 5}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=product)

    install_transport(monkeypatch, handler)

    result = await get_product("product-1")

    assert result == product
    assert len(calls) == 1
    assert str(calls[0].url) == f"{settings.PRODUCTS_SERVICE_URL}/products/product-1"


async def test_get_product_raises_invalid_product_without_retry(monkeypatch, no_sleep) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(404)

    install_transport(monkeypatch, handler)

    with pytest.raises(InvalidProductIdError):
        await get_product("missing")

    assert len(calls) == 1
    no_sleep.assert_not_awaited()


async def test_get_product_raises_client_error_without_retry(monkeypatch, no_sleep) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(400)

    install_transport(monkeypatch, handler)

    with pytest.raises(httpx.HTTPStatusError):
        await get_product("product-1")

    assert len(calls) == 1
    no_sleep.assert_not_awaited()


async def test_get_product_retries_server_error(monkeypatch, no_sleep) -> None:
    statuses = [500, 200]
    calls = []
    product = {"id": "product-1", "name": "apple", "price": 10.0, "quantity": 5}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        status = statuses.pop(0)
        if status == 200:
            return httpx.Response(status, json=product)
        return httpx.Response(status)

    install_transport(monkeypatch, handler)

    assert await get_product("product-1") == product
    assert len(calls) == 2
    no_sleep.assert_awaited_once()


async def test_get_product_retries_too_many_requests(monkeypatch) -> None:
    statuses = [429, 200]
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(statuses.pop(0), json={})

    install_transport(monkeypatch, handler)

    await get_product("product-1")

    assert len(calls) == 2


async def test_get_product_raises_after_exhausting_attempts(monkeypatch) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(500)

    install_transport(monkeypatch, handler)

    with pytest.raises(httpx.HTTPStatusError):
        await get_product("product-1")

    assert len(calls) == settings.MAX_ATTEMPTS


async def test_get_product_retries_transport_error(monkeypatch) -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, json={})

    install_transport(monkeypatch, handler)

    await get_product("product-1")

    assert attempts["count"] == 2


async def test_get_product_raises_after_transport_errors(monkeypatch) -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        raise httpx.ConnectError("boom", request=request)

    install_transport(monkeypatch, handler)

    with pytest.raises(httpx.ConnectError):
        await get_product("product-1")

    assert attempts["count"] == settings.MAX_ATTEMPTS


async def test_lock_products_sends_single_request(monkeypatch, no_sleep) -> None:
    calls = []
    product_id = uuid.uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"success": True})

    install_transport(monkeypatch, handler)

    await lock_products({product_id: 2})

    assert len(calls) == 1
    assert str(calls[0].url) == f"{settings.PRODUCTS_SERVICE_URL}/internal/products/lock"
    assert calls[0].method == "POST"
    assert json.loads(calls[0].content) == [{"product_id": str(product_id), "quantity": 2}]
    no_sleep.assert_not_awaited()


async def test_lock_products_maps_404_to_invalid_product(monkeypatch, no_sleep) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(404)

    install_transport(monkeypatch, handler)

    with pytest.raises(InvalidProductIdError):
        await lock_products({uuid.uuid4(): 1})

    assert len(calls) == 1
    no_sleep.assert_not_awaited()


async def test_lock_products_maps_409_to_not_enough_quantity(monkeypatch) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(409)

    install_transport(monkeypatch, handler)

    with pytest.raises(NotEnoughProductQuantityError):
        await lock_products({uuid.uuid4(): 1})

    assert len(calls) == 1


async def test_lock_products_raises_other_client_error_without_retry(monkeypatch, no_sleep) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(400)

    install_transport(monkeypatch, handler)

    with pytest.raises(httpx.HTTPStatusError):
        await lock_products({uuid.uuid4(): 1})

    assert len(calls) == 1
    no_sleep.assert_not_awaited()


async def test_lock_products_does_not_retry_server_error(monkeypatch, no_sleep) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(500)

    install_transport(monkeypatch, handler)

    with pytest.raises(httpx.HTTPStatusError):
        await lock_products({uuid.uuid4(): 1})

    assert len(calls) == 1
    no_sleep.assert_not_awaited()


async def test_unlock_products_sends_single_request(monkeypatch) -> None:
    calls = []
    product_id = uuid.uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"success": True})

    install_transport(monkeypatch, handler)

    await unlock_products({product_id: 3})

    assert len(calls) == 1
    assert str(calls[0].url) == f"{settings.PRODUCTS_SERVICE_URL}/internal/products/unlock"
    assert calls[0].method == "POST"
    assert json.loads(calls[0].content) == [{"product_id": str(product_id), "quantity": 3}]


async def test_unlock_products_swallows_status_errors(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    install_transport(monkeypatch, handler)

    await unlock_products({uuid.uuid4(): 1})


async def test_unlock_products_swallows_transport_errors(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    install_transport(monkeypatch, handler)

    await unlock_products({uuid.uuid4(): 1})
