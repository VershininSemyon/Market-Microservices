
import uuid
from unittest.mock import AsyncMock

from src.enums import ProductSortFieldEnum, SortOrderEnum
from src.exceptions import ProductNotFoundError
from src.schemas import ProductReadSchema


def product_payload(product: ProductReadSchema) -> dict:
    return product.model_dump(mode="json")


async def test_list_products(client, product_service: AsyncMock, sample_product: ProductReadSchema) -> None:
    product_service.get_products_list.return_value = [sample_product]

    response = await client.get("/products/")

    assert response.status_code == 200
    assert response.json() == [product_payload(sample_product)]
    product_service.get_products_list.assert_awaited_once()


async def test_list_products_passes_filters(client, product_service: AsyncMock) -> None:
    product_service.get_products_list.return_value = []

    response = await client.get(
        "/products/",
        params={
            "text_query": "apple",
            "min_price": 1,
            "max_price": 10,
            "order_by": "price",
            "order": "desc",
            "limit": 5,
            "offset": 2,
        },
    )

    assert response.status_code == 200
    filters = product_service.get_products_list.call_args.args[0]
    assert filters.text_query == "apple"
    assert filters.min_price == 1.0
    assert filters.max_price == 10.0
    assert filters.order_by == ProductSortFieldEnum.PRICE
    assert filters.order == SortOrderEnum.DESC
    assert filters.limit == 5
    assert filters.offset == 2


async def test_list_products_rejects_invalid_price_range(client, product_service: AsyncMock) -> None:
    response = await client.get("/products/", params={"min_price": 10, "max_price": 5})

    assert response.status_code == 422
    product_service.get_products_list.assert_not_awaited()


async def test_list_products_rejects_invalid_limit(client, product_service: AsyncMock) -> None:
    response = await client.get("/products/", params={"limit": 0})

    assert response.status_code == 422
    product_service.get_products_list.assert_not_awaited()


async def test_create_product_as_admin(
    admin_client,
    admin_user,
    product_service: AsyncMock,
    sample_product: ProductReadSchema,
) -> None:
    product_service.create_product.return_value = sample_product

    response = await admin_client.post(
        "/products/",
        json={
            "name": "apple",
            "description": "green apple",
            "price": 10.0,
            "quantity": 5,
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "apple"
    product_service.create_product.assert_awaited_once()
    data, user_email = product_service.create_product.call_args.args
    assert data.name == "apple"
    assert user_email == admin_user.email


async def test_create_product_forbidden_for_regular_user(
    user_client,
    product_service: AsyncMock,
) -> None:
    response = await user_client.post(
        "/products/",
        json={"name": "apple", "price": 10.0, "quantity": 5},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Доступ запрещён"}
    product_service.create_product.assert_not_awaited()


async def test_create_product_requires_authorization(client, product_service: AsyncMock) -> None:
    response = await client.post(
        "/products/",
        json={"name": "apple", "price": 10.0, "quantity": 5},
    )

    assert response.status_code == 401
    product_service.create_product.assert_not_awaited()


async def test_create_product_validates_body(
    admin_client,
    product_service: AsyncMock,
) -> None:
    response = await admin_client.post(
        "/products/",
        json={"name": "apple", "price": 0, "quantity": -1},
    )

    assert response.status_code == 422
    product_service.create_product.assert_not_awaited()


async def test_get_product(client, product_service: AsyncMock, sample_product: ProductReadSchema) -> None:
    product_service.get_product_by_id.return_value = sample_product

    response = await client.get(f"/products/{sample_product.id}")

    assert response.status_code == 200
    assert response.json() == product_payload(sample_product)
    product_service.get_product_by_id.assert_awaited_once_with(sample_product.id)


async def test_get_product_returns_not_found(client, product_service: AsyncMock) -> None:
    product_service.get_product_by_id.side_effect = ProductNotFoundError()

    response = await client.get(f"/products/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Продукт не найден"}


async def test_get_product_rejects_invalid_uuid(client, product_service: AsyncMock) -> None:
    response = await client.get("/products/not-a-uuid")

    assert response.status_code == 422
    product_service.get_product_by_id.assert_not_awaited()


async def test_update_product_as_admin(
    admin_client,
    product_service: AsyncMock,
    sample_product: ProductReadSchema,
) -> None:
    product_service.update_product.return_value = sample_product

    response = await admin_client.put(
        f"/products/{sample_product.id}",
        json={"name": "apple", "description": None, "price": 12.0, "quantity": 3},
    )

    assert response.status_code == 200
    product_service.update_product.assert_awaited_once()
    product_id, data = product_service.update_product.call_args.args
    assert product_id == sample_product.id
    assert data.price == 12.0


async def test_update_product_forbidden_for_regular_user(
    user_client,
    product_service: AsyncMock,
) -> None:
    response = await user_client.put(
        f"/products/{uuid.uuid4()}",
        json={"name": "apple", "description": None, "price": 12.0, "quantity": 3},
    )

    assert response.status_code == 403
    product_service.update_product.assert_not_awaited()


async def test_update_product_returns_not_found(admin_client, product_service: AsyncMock) -> None:
    product_service.update_product.side_effect = ProductNotFoundError()

    response = await admin_client.put(
        f"/products/{uuid.uuid4()}",
        json={"name": "apple", "description": None, "price": 12.0, "quantity": 3},
    )

    assert response.status_code == 404


async def test_delete_product_as_admin(
    admin_client,
    admin_user,
    product_service: AsyncMock,
) -> None:
    product_id = uuid.uuid4()

    response = await admin_client.delete(f"/products/{product_id}")

    assert response.status_code == 204
    product_service.delete_product.assert_awaited_once_with(product_id, admin_user.email)


async def test_delete_product_forbidden_for_regular_user(
    user_client,
    product_service: AsyncMock,
) -> None:
    response = await user_client.delete(f"/products/{uuid.uuid4()}")

    assert response.status_code == 403
    product_service.delete_product.assert_not_awaited()


async def test_delete_product_returns_not_found(admin_client, product_service: AsyncMock) -> None:
    product_service.delete_product.side_effect = ProductNotFoundError()

    response = await admin_client.delete(f"/products/{uuid.uuid4()}")

    assert response.status_code == 404
