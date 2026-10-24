
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

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
    product_ids: list[uuid.UUID]
    pass
