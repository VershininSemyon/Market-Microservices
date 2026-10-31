
import asyncio
import uuid
from datetime import date

from src.config import settings
from src.exceptions import NotEnoughProductQuantityError, OrderNotFoundError, OrderOwnershipError
from src.models import ExchangeTypeEnum
from src.products_api_client import get_product
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

    async def create_order(self, user_id: uuid.UUID, user_email: str, data: OrderCreateSchema) -> OrderReadSchema:
        products = {}
        total_price = 0.0
        total_amount = 0

        api_products = await asyncio.gather(*(
            get_product(product_id)
            for product_id in data.products.keys()
        ))

        for product, quantity in zip(api_products, data.products.values()):
            if product["quantity"] < quantity:
                raise NotEnoughProductQuantityError()

            products[product["id"]] = {
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity
            }

            total_price += product["price"] * quantity
            total_amount += quantity

        async with self.uow:
            order = await self.uow.order_repo.create_order(
                {
                    "user_id": user_id,
                    "products": products,
                    "total_price": total_price,
                    "total_amount": total_amount
                }
            )

            event_data = {
                "exchange_name": settings.ORDERS_EVENTS_EXCHANGE_NAME,
                "exchange_type": ExchangeTypeEnum.TOPIC,
                "routing_key": settings.ORDER_CREATED_ROUTING_KEY,
                "event_payload": {
                    "event_id": str(uuid.uuid4()),
                    "total_amount": total_amount,
                    "total_price": total_price,
                    "products": [
                        {
                            "id": str(prod_id),
                            "quantity": prod_data["quantity"]
                        }
                        for prod_id, prod_data in products.items()
                    ],
                    "event_date": str(date.today()),
                    "user_email": user_email
                }
            }

            await self.uow.outbox_repo.create_outbox_event(event_data)

            await self.uow.commit()

        return OrderReadSchema.model_validate(order)
