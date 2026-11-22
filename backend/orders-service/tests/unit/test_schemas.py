
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.schemas import OrderCreateSchema, OrderProduct, OrderReadSchema


def test_order_create_schema_accepts_valid_products() -> None:
    product_id = uuid.uuid4()

    data = OrderCreateSchema(products={product_id: 2})

    assert data.products == {product_id: 2}


def test_order_create_schema_coerces_string_keys() -> None:
    product_id = uuid.uuid4()

    data = OrderCreateSchema(products={str(product_id): 3})

    assert data.products == {product_id: 3}


def test_order_create_schema_rejects_empty_products() -> None:
    with pytest.raises(ValidationError):
        OrderCreateSchema(products={})


def test_order_create_schema_rejects_non_positive_quantity() -> None:
    with pytest.raises(ValidationError):
        OrderCreateSchema(products={uuid.uuid4(): 0})

    with pytest.raises(ValidationError):
        OrderCreateSchema(products={uuid.uuid4(): -1})


def test_order_read_schema_parses_stored_products() -> None:
    order_id = uuid.uuid4()
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()

    order = OrderReadSchema.model_validate(
        {
            "id": order_id,
            "user_id": user_id,
            "products": {
                str(product_id): {"name": "apple", "price": 10.0, "quantity": 2}
            },
            "total_price": 20.0,
            "total_amount": 2,
            "created_at": datetime.now(timezone.utc),
        }
    )

    assert order.products[product_id] == OrderProduct(name="apple", price=10.0, quantity=2)
