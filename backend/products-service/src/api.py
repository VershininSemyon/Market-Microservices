
from typing import Annotated

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
