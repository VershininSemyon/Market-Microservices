
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

OrderTotalPrice = Annotated[float, Field(gt=0)]
OrderTotalAmount = Annotated[int, Field(ge=0)]


class OrderProduct(BaseModel):
    name: str
    price: float
    quantity: int


class OrderReadSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    products: dict[uuid.UUID, OrderProduct]
    total_price: OrderTotalPrice
    total_amount: OrderTotalAmount
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderCreateSchema(BaseModel):
    products: dict[uuid.UUID, int]

    @classmethod
    @field_validator("products")
    def validate_products(cls, value):
        if not value:
            raise ValueError("Список товаров не может быть пустым")

        for product_id, quantity in value.items():
            if quantity <= 0:
                raise ValueError(f"Количество товара с id {product_id} должно быть больше нуля")

        return value
