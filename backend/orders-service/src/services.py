
import uuid

from src.exceptions import OrderNotFoundError, OrderOwnershipError
from src.schemas import OrderCreateSchema, OrderReadSchema
from src.unitofwork import UnitOfWork


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_user_orders(self, user_id: uuid.UUID) -> list[OrderReadSchema]:
        async with self.uow:
            orders = await self.uow.order_repo.get_orders_by_user_id(user_id)

        return [OrderReadSchema.model_validate(order) for order in orders]

    async def get_order_by_id(self, user_id: uuid.UUID, order_id: uuid.UUID) -> OrderReadSchema:
        async with self.uow:
            order = await self.uow.order_repo.get_order_by_id(order_id)

        if not order:
            raise OrderNotFoundError()

        if order.user_id != user_id:
            raise OrderOwnershipError()

        return OrderReadSchema.model_validate(order)

