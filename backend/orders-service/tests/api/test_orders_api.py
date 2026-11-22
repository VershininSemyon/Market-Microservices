
import uuid
from unittest.mock import AsyncMock

from src.exceptions import OrderNotFoundError, OrderOwnershipError
from src.schemas import OrderReadSchema


def order_payload(order: OrderReadSchema) -> dict:
    return order.model_dump(mode="json")


async def test_get_user_orders(
    authenticated_client,
    current_user,
    order_service: AsyncMock,
    sample_order: OrderReadSchema,
) -> None:
    order_service.get_user_orders.return_value = [sample_order]

    response = await authenticated_client.get("/orders/")

    assert response.status_code == 200
    assert response.json() == [order_payload(sample_order)]
    order_service.get_user_orders.assert_awaited_once_with(current_user.id)


async def test_get_user_orders_requires_authorization(client, order_service: AsyncMock) -> None:
    response = await client.get("/orders/")

    assert response.status_code == 401
    order_service.get_user_orders.assert_not_awaited()


async def test_create_order(
    authenticated_client,
    current_user,
    order_service: AsyncMock,
    sample_order: OrderReadSchema,
) -> None:
    order_service.create_order.return_value = sample_order
    product_id = uuid.uuid4()

    response = await authenticated_client.post(
        "/orders/",
        json={"products": {str(product_id): 2}},
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(sample_order.id)
    order_service.create_order.assert_awaited_once()
    user_id, user_email, data = order_service.create_order.call_args.args
    assert user_id == current_user.id
    assert user_email == current_user.email
    assert data.products == {product_id: 2}


async def test_create_order_requires_authorization(client, order_service: AsyncMock) -> None:
    response = await client.post(
        "/orders/",
        json={"products": {str(uuid.uuid4()): 1}},
    )

    assert response.status_code == 401
    order_service.create_order.assert_not_awaited()


async def test_create_order_rejects_empty_products(
    authenticated_client,
    order_service: AsyncMock,
) -> None:
    response = await authenticated_client.post("/orders/", json={"products": {}})

    assert response.status_code == 422
    order_service.create_order.assert_not_awaited()


async def test_create_order_rejects_non_positive_quantity(
    authenticated_client,
    order_service: AsyncMock,
) -> None:
    response = await authenticated_client.post(
        "/orders/",
        json={"products": {str(uuid.uuid4()): 0}},
    )

    assert response.status_code == 422
    order_service.create_order.assert_not_awaited()


async def test_get_order_by_id(
    authenticated_client,
    current_user,
    order_service: AsyncMock,
    sample_order: OrderReadSchema,
) -> None:
    order_service.get_order_by_id.return_value = sample_order

    response = await authenticated_client.get(f"/orders/{sample_order.id}")

    assert response.status_code == 200
    assert response.json() == order_payload(sample_order)
    order_service.get_order_by_id.assert_awaited_once_with(current_user.id, sample_order.id)


async def test_get_order_by_id_requires_authorization(client, order_service: AsyncMock) -> None:
    response = await client.get(f"/orders/{uuid.uuid4()}")

    assert response.status_code == 401
    order_service.get_order_by_id.assert_not_awaited()


async def test_get_order_by_id_returns_not_found(authenticated_client, order_service: AsyncMock) -> None:
    order_service.get_order_by_id.side_effect = OrderNotFoundError()

    response = await authenticated_client.get(f"/orders/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Заказ не найден"}


async def test_get_order_by_id_returns_forbidden_for_non_owner(
    authenticated_client,
    order_service: AsyncMock,
) -> None:
    order_service.get_order_by_id.side_effect = OrderOwnershipError()

    response = await authenticated_client.get(f"/orders/{uuid.uuid4()}")

    assert response.status_code == 403
    assert response.json() == {"detail": "Вы не являетесь создателем этого заказа"}


async def test_get_order_by_id_rejects_invalid_uuid(
    authenticated_client,
    order_service: AsyncMock,
) -> None:
    response = await authenticated_client.get("/orders/not-a-uuid")

    assert response.status_code == 422
    order_service.get_order_by_id.assert_not_awaited()
