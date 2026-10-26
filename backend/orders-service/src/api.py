
import uuid

from fastapi import APIRouter, status

from src.dependencies import CurrentUserDep, OrderServiceDep
from src.schemas import OrderCreateSchema, OrderReadSchema

order_router = APIRouter(prefix="/orders", tags=["Orders"])


@order_router.get(
    "/",
    response_model=list[OrderReadSchema],
    status_code=status.HTTP_200_OK,
)
async def get_user_orders(
    orders_service: OrderServiceDep,
    user: CurrentUserDep,
) -> list[OrderReadSchema]:
    return await orders_service.get_user_orders(user.id)


@order_router.post(
    "/",
    response_model=OrderReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    data: OrderCreateSchema,
    orders_service: OrderServiceDep,
    user: CurrentUserDep
) -> OrderReadSchema:
    return await orders_service.create_order(user.id, user.email, data)


@order_router.get(
    "/{order_id}",
    response_model=OrderReadSchema,
    status_code=status.HTTP_200_OK,
)
async def get_order_by_id(
    order_id: uuid.UUID,
    orders_service: OrderServiceDep,
    user: CurrentUserDep
) -> OrderReadSchema:
    return await orders_service.get_order_by_id(user.id, order_id)
