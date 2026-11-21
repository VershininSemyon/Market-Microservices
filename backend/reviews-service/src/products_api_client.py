
import asyncio

import httpx

from src.config import settings
from src.exceptions import ProductNotFoundError


async def check_product_exists(product_id: str) -> None:
    timeout = httpx.Timeout(settings.REQUEST_TIMEOUT, connect=settings.CONNECT_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(settings.MAX_ATTEMPTS):
            try:
                response = await client.get(f"{settings.PRODUCTS_SERVICE_URL}/products/{product_id}")
                response.raise_for_status()
                return
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    raise ProductNotFoundError()
                if exc.response.status_code < 500 and exc.response.status_code != 429:
                    raise
                if attempt == settings.MAX_ATTEMPTS - 1:
                    raise
            except httpx.TransportError:
                if attempt == settings.MAX_ATTEMPTS - 1:
                    raise

            await asyncio.sleep(settings.RETRY_PAUSE_SECONDS * 2 ** attempt)

    raise RuntimeError("Не удалось проверить существование товара")
