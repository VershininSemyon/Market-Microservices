
import uuid
from unittest.mock import AsyncMock

from src.exceptions import (
    DuplicateProductIdError,
    NotEnoughProductQuantityError,
    ProductNotFoundError,
)


async def test_lock_products_returns_success(client, product_service: AsyncMock) -> None:
    product_id = uuid.uuid4()

    response = await client.post(
        "/internal/products/lock",
        json=[{"product_id": str(product_id), "quantity": 2}],
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    items = product_service.lock_products.call_args.args[0]
    assert len(items) == 1
    assert items[0].product_id == product_id
    assert items[0].quantity == 2


async def test_unlock_products_returns_success(client, product_service: AsyncMock) -> None:
    product_id = uuid.uuid4()

    response = await client.post(
        "/internal/products/unlock",
        json=[{"product_id": str(product_id), "quantity": 2}],
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    items = product_service.unlock_products.call_args.args[0]
    assert len(items) == 1
    assert items[0].product_id == product_id
    assert items[0].quantity == 2


async def test_lock_products_rejects_empty_list(client, product_service: AsyncMock) -> None:
    response = await client.post("/internal/products/lock", json=[])

    assert response.status_code == 422
    product_service.lock_products.assert_not_awaited()


async def test_unlock_products_rejects_empty_list(client, product_service: AsyncMock) -> None:
    response = await client.post("/internal/products/unlock", json=[])

    assert response.status_code == 422
    product_service.unlock_products.assert_not_awaited()


async def test_lock_products_rejects_non_positive_quantity(client, product_service: AsyncMock) -> None:
    response = await client.post(
        "/internal/products/lock",
        json=[{"product_id": str(uuid.uuid4()), "quantity": 0}],
    )

    assert response.status_code == 422
    product_service.lock_products.assert_not_awaited()


async def test_unlock_products_rejects_non_positive_quantity(client, product_service: AsyncMock) -> None:
    response = await client.post(
        "/internal/products/unlock",
        json=[{"product_id": str(uuid.uuid4()), "quantity": -1}],
    )

    assert response.status_code == 422
    product_service.unlock_products.assert_not_awaited()


async def test_lock_products_maps_duplicate_error_to_400(client, product_service: AsyncMock) -> None:
    product_service.lock_products.side_effect = DuplicateProductIdError()

    response = await client.post(
        "/internal/products/lock",
        json=[{"product_id": str(uuid.uuid4()), "quantity": 1}],
    )

    assert response.status_code == 400


async def test_lock_products_maps_not_found_error_to_404(client, product_service: AsyncMock) -> None:
    product_service.lock_products.side_effect = ProductNotFoundError()

    response = await client.post(
        "/internal/products/lock",
        json=[{"product_id": str(uuid.uuid4()), "quantity": 1}],
    )

    assert response.status_code == 404


async def test_lock_products_maps_not_enough_quantity_error_to_409(client, product_service: AsyncMock) -> None:
    product_service.lock_products.side_effect = NotEnoughProductQuantityError()

    response = await client.post(
        "/internal/products/lock",
        json=[{"product_id": str(uuid.uuid4()), "quantity": 1}],
    )

    assert response.status_code == 409
