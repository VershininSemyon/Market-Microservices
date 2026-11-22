
import pytest
from pydantic import ValidationError

from src.schemas import (
    OrderCreatedMessage,
    ProductCreatedMessage,
    ProductDeletedMessage,
    ReviewMessage,
    UserCreatedMessage,
    UserDeletedMessage,
)


def test_user_created_message() -> None:
    message = UserCreatedMessage.model_validate(
        {"username": "alice", "email": "alice@example.com"}
    )

    assert message.username == "alice"
    assert message.email == "alice@example.com"


def test_user_deleted_message() -> None:
    message = UserDeletedMessage.model_validate({"email": "alice@example.com"})

    assert message.email == "alice@example.com"


def test_product_created_message() -> None:
    message = ProductCreatedMessage.model_validate(
        {"product_name": "apple", "created_by": "alice@example.com"}
    )

    assert message.product_name == "apple"
    assert message.created_by == "alice@example.com"


def test_product_deleted_message() -> None:
    message = ProductDeletedMessage.model_validate(
        {"product_name": "apple", "deleted_by": "alice@example.com"}
    )

    assert message.product_name == "apple"
    assert message.deleted_by == "alice@example.com"


def test_review_message() -> None:
    message = ReviewMessage.model_validate(
        {"product_id": "product-1", "user_email": "alice@example.com"}
    )

    assert message.product_id == "product-1"
    assert message.user_email == "alice@example.com"


def test_order_created_message() -> None:
    message = OrderCreatedMessage.model_validate(
        {"total_price": 20.5, "total_amount": 2, "user_email": "alice@example.com"}
    )

    assert message.total_price == 20.5
    assert message.total_amount == 2
    assert message.user_email == "alice@example.com"


@pytest.mark.parametrize(
    ("schema", "payload"),
    [
        (UserCreatedMessage, {"username": "alice", "email": "not-an-email"}),
        (UserDeletedMessage, {"email": "not-an-email"}),
        (ProductCreatedMessage, {"product_name": "apple"}),
        (ProductDeletedMessage, {"deleted_by": "alice@example.com"}),
        (ReviewMessage, {"product_id": "product-1"}),
        (OrderCreatedMessage, {"total_price": 20.5, "user_email": "alice@example.com"}),
    ],
)
def test_messages_reject_invalid_payloads(schema, payload) -> None:
    with pytest.raises(ValidationError):
        schema.model_validate(payload)


def test_order_created_message_requires_numeric_price() -> None:
    with pytest.raises(ValidationError):
        OrderCreatedMessage.model_validate(
            {
                "total_price": "not-a-number",
                "total_amount": 2,
                "user_email": "alice@example.com",
            }
        )
