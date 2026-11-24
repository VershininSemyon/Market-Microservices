
from typing import Any
from uuid import UUID

from redis import asyncio

from src.redis_manager import redis_manager


def get_lock_key(product_id: UUID | str) -> str:
    return f"products:{product_id}:lock"


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

    async def incrby(self, key: str, amount: int) -> int:
        return int(await self.client.incrby(key, amount))

    async def decrby(self, key: str, amount: int) -> int:
        return int(await self.client.decrby(key, amount))

    async def release_lock(self, key: str, amount: int) -> None:
        value = await self.decrby(key, amount)
        if value <= 0:
            await self.del_key(key)


redis_cache = RedisCacheBackend()

