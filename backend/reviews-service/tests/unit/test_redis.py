
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.redis_manager as redis_manager_module
from src.config import settings
from src.redis_cache_backend import RedisCacheBackend
from src.redis_manager import RedisManager, redis_manager


def test_client_raises_when_not_connected() -> None:
    manager = RedisManager()

    with pytest.raises(RuntimeError, match="Redis"):
        _ = manager.client


async def test_connect_creates_client_and_pings(monkeypatch) -> None:
    fake_client = AsyncMock()
    fake_client.ping = AsyncMock()
    from_url = MagicMock(return_value=fake_client)
    monkeypatch.setattr(redis_manager_module, "asyncio", SimpleNamespace(from_url=from_url))

    manager = RedisManager()
    await manager.connect()

    from_url.assert_called_once_with(
        settings.redis_url,
        decode_responses=True,
        max_connections=50,
    )
    fake_client.ping.assert_awaited_once()
    assert manager.client is fake_client


async def test_connect_does_not_recreate_existing_client(monkeypatch) -> None:
    fake_client = AsyncMock()
    fake_client.ping = AsyncMock()
    from_url = MagicMock(return_value=fake_client)
    monkeypatch.setattr(redis_manager_module, "asyncio", SimpleNamespace(from_url=from_url))

    manager = RedisManager()
    await manager.connect()
    await manager.connect()

    from_url.assert_called_once()


async def test_disconnect_closes_client() -> None:
    fake_client = AsyncMock()
    fake_client.close = AsyncMock()
    redis_manager._client = fake_client

    manager = RedisManager()
    await manager.disconnect()

    fake_client.close.assert_awaited_once()
    assert redis_manager._client is None


async def test_disconnect_without_client_does_nothing() -> None:
    manager = RedisManager()

    await manager.disconnect()

    assert redis_manager._client is None


async def test_cache_set_value_with_ttl() -> None:
    fake_client = AsyncMock()
    redis_manager._client = fake_client
    cache = RedisCacheBackend()

    await cache.set_value("key", "value", 60)

    fake_client.set.assert_awaited_once_with("key", "value", ex=60)


async def test_cache_set_value_without_ttl() -> None:
    fake_client = AsyncMock()
    redis_manager._client = fake_client
    cache = RedisCacheBackend()

    await cache.set_value("key", "value")

    fake_client.set.assert_awaited_once_with("key", "value", ex=None)


async def test_cache_get_value() -> None:
    fake_client = AsyncMock()
    fake_client.get.return_value = "value"
    redis_manager._client = fake_client
    cache = RedisCacheBackend()

    result = await cache.get_value("key")

    assert result == "value"
    fake_client.get.assert_awaited_once_with("key")


async def test_cache_del_key() -> None:
    fake_client = AsyncMock()
    redis_manager._client = fake_client
    cache = RedisCacheBackend()

    await cache.del_key("key")

    fake_client.delete.assert_awaited_once_with("key")
