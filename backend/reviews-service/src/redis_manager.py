
from redis import asyncio

from src.config import settings


class RedisManager:
    _instance: "RedisManager | None" = None
    _client: asyncio.Redis | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance

    @property
    def client(self) -> asyncio.Redis:
        if self._client is None:
            raise RuntimeError("Не инициализирован Redis клиент")
        return self._client

    async def connect(self) -> None:
        if self._client is None:
            self._client = asyncio.from_url(
                settings.redis_url,
                decode_responses=True,
                max_connections=50,
            )

            await self._client.ping()

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None


redis_manager = RedisManager()
