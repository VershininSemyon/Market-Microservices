
from unittest.mock import AsyncMock

import httpx
import pytest

import src.products_api_client as client_module
from src.config import settings
from src.exceptions import ProductNotFoundError
from src.products_api_client import check_product_exists

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


async def test_check_product_exists_success(monkeypatch) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"id": "product-1"})

    install_transport(monkeypatch, handler)

    await check_product_exists("product-1")

    assert len(calls) == 1
    assert str(calls[0].url) == f"{settings.PRODUCTS_SERVICE_URL}/products/product-1"


async def test_check_product_exists_raises_not_found_without_retry(monkeypatch, no_sleep) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(404)

    install_transport(monkeypatch, handler)

    with pytest.raises(ProductNotFoundError):
        await check_product_exists("missing")

    assert len(calls) == 1
    no_sleep.assert_not_awaited()


async def test_check_product_exists_raises_client_error_without_retry(monkeypatch, no_sleep) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(400)

    install_transport(monkeypatch, handler)

    with pytest.raises(httpx.HTTPStatusError):
        await check_product_exists("product-1")

    assert len(calls) == 1
    no_sleep.assert_not_awaited()


async def test_check_product_exists_retries_server_error(monkeypatch, no_sleep) -> None:
    statuses = [500, 200]
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(statuses.pop(0))

    install_transport(monkeypatch, handler)

    await check_product_exists("product-1")

    assert len(calls) == 2
    no_sleep.assert_awaited_once()


async def test_check_product_exists_retries_too_many_requests(monkeypatch) -> None:
    statuses = [429, 200]
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(statuses.pop(0))

    install_transport(monkeypatch, handler)

    await check_product_exists("product-1")

    assert len(calls) == 2


async def test_check_product_exists_raises_after_exhausting_attempts(monkeypatch) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(500)

    install_transport(monkeypatch, handler)

    with pytest.raises(httpx.HTTPStatusError):
        await check_product_exists("product-1")

    assert len(calls) == settings.MAX_ATTEMPTS


async def test_check_product_exists_retries_transport_error(monkeypatch) -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200)

    install_transport(monkeypatch, handler)

    await check_product_exists("product-1")

    assert attempts["count"] == 2


async def test_check_product_exists_raises_after_transport_errors(monkeypatch) -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        raise httpx.ConnectError("boom", request=request)

    install_transport(monkeypatch, handler)

    with pytest.raises(httpx.ConnectError):
        await check_product_exists("product-1")

    assert attempts["count"] == settings.MAX_ATTEMPTS
