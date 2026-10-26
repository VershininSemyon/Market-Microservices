
import uuid

import httpx

from src.exceptions import InvalidProductIdError


async def get_product(product_id: uuid.UUID) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://products-backend:8002/products/{product_id}")

        if response.status_code == 404:
            raise InvalidProductIdError()

        data = response.json()
        return data
