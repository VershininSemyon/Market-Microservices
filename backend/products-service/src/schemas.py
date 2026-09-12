

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.enums import ProductSortFieldEnum, SortOrderEnum

ProductName = Annotated[str, Field(max_length=200)]
ProductPrice = Annotated[float, Field(gt=0)]
ProductQuantity = Annotated[int, Field(ge=0)]


class ProductReadSchema(BaseModel):
    id: uuid.UUID
    name: ProductName
    description: str | None
    price: ProductPrice
    quantity: ProductQuantity
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductCreateSchema(BaseModel):
    name: ProductName
    description: str | None = None
    price: ProductPrice
    quantity: ProductQuantity


class ProductUpdateSchema(BaseModel):
    name: ProductName
    description: str | None
    price: ProductPrice
    quantity: ProductQuantity


class ProductQueryParams(BaseModel):
    text_query: str | None = None
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)
    order_by: ProductSortFieldEnum | None = None
    order: SortOrderEnum = SortOrderEnum.ASC
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate(self):
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("Минимальная цена не может быть больше максимальной")
        return self
