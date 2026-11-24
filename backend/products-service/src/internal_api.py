
from typing import Annotated

from fastapi import APIRouter, Body, status

from src.dependencies import ProductServiceDep
from src.schemas import LockProductSchema, LockProductsResponseSchema

internal_product_router = APIRouter(prefix="/internal/products", tags=["Internal Products"])


@internal_product_router.post(
    "/lock",
    response_model=LockProductsResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def lock_products(
    data: Annotated[list[LockProductSchema], Body(min_length=1)],
    product_service: ProductServiceDep,
) -> LockProductsResponseSchema:
    await product_service.lock_products(data)
    return LockProductsResponseSchema(success=True)


@internal_product_router.post(
    "/unlock",
    response_model=LockProductsResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def unlock_products(
    data: Annotated[list[LockProductSchema], Body(min_length=1)],
    product_service: ProductServiceDep,
) -> LockProductsResponseSchema:
    await product_service.unlock_products(data)
    return LockProductsResponseSchema(success=True)
