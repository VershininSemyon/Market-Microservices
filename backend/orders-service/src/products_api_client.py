
import asyncio
import uuid

import httpx

from src.config import settings
from src.exceptions import InvalidProductIdError


async def get_product(product_id: uuid.UUID) -> dict:
    timeout = httpx.Timeout(settings.REQUEST_TIMEOUT, connect=settings.CONNECT_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(settings.MAX_ATTEMPTS):
            try:
                response = await client.get(f"{settings.PRODUCTS_SERVICE_URL}/products/{product_id}")
                response.raise_for_status()
                data = response.json()
                return data
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    raise InvalidProductIdError()
                if exc.response.status_code < 500 and exc.response.status_code != 429:
                    raise
                if attempt == settings.MAX_ATTEMPTS - 1:
                    raise
            except httpx.TransportError:
                if attempt == settings.MAX_ATTEMPTS - 1:
                    raise

            await asyncio.sleep(settings.RETRY_PAUSE_SECONDS * 2 ** attempt)

    raise RuntimeError("Не удалось получить данные товара")
