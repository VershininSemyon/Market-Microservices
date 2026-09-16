
import httpx

from src.exceptions import ProductNotFoundError


async def check_product_exists(product_id: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://products-backend:8002/products/{product_id}")

        if response.status_code == 404:
            raise ProductNotFoundError()
