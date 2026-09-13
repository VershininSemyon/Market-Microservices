
from typing import Annotated

from uuid import UUID
from fastapi import APIRouter, Depends, status

from src.dependencies import CurrentUserDep, ProductServiceDep, require_admin
from src.schemas import ProductCreateSchema, ProductQueryParams, ProductReadSchema, ProductUpdateSchema

product_router = APIRouter(prefix="/products", tags=["Products"])


@product_router.post(
    "/",
    response_model=ProductReadSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_product(
    data: ProductCreateSchema,
    product_service: ProductServiceDep,
) -> ProductReadSchema:
    return await product_service.create_product(data)


@product_router.get(
    "/",
    response_model=list[ProductReadSchema],
    status_code=status.HTTP_200_OK,
)
async def list_products(
    filters: Annotated[ProductQueryParams, Depends()],
    product_service: ProductServiceDep,
) -> list[ProductReadSchema]:
    return await product_service.get_products_list(filters)


@product_router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_product(
    product_id: UUID,
    product_service: ProductServiceDep,
) -> None:
    await product_service.delete_product(product_id)


@product_router.get(
    "/{product_id}",
    response_model=ProductReadSchema,
    status_code=status.HTTP_200_OK,
)
async def get_product(
    product_id: UUID,
    product_service: ProductServiceDep,
) -> ProductReadSchema:
    return await product_service.get_product_by_id(product_id)


@product_router.put(
    "/{product_id}",
    response_model=ProductReadSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)],
)
async def update_product(
    product_id: UUID,
    data: ProductUpdateSchema,
    product_service: ProductServiceDep,
) -> ProductReadSchema:
    return await product_service.update_product(product_id, data)
