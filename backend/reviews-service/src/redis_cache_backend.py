
from typing import Any

from redis import asyncio

from src.redis_manager import redis_manager


class RedisCacheBackend:
    @property
    def client(self) -> asyncio.Redis:
        return redis_manager.client

    async def set_value(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.client.set(key, value, ex=ttl)

    async def get_value(self, key: str) -> str | None:
        return await self.client.get(key)

    async def del_key(self, key: str) -> None:
        await self.client.delete(key)


redis_cache = RedisCacheBackend()
