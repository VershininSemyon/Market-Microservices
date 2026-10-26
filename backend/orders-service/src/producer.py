
import uuid
from datetime import date

from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange
from pydantic import BaseModel

from src.config import settings


class OrderProductEventItem(BaseModel):
    id: uuid.UUID
    quantity: int


class OrderCreatedEventPayload(BaseModel):
    total_amount: int
    total_price: float
    products: list[OrderProductEventItem]
    event_date: date
    user_email: str


broker = RabbitBroker(settings.amqp_url)

orders_events_exchange = RabbitExchange(
    name=settings.ORDERS_EVENTS_EXCHANGE_NAME,
    type=ExchangeType.TOPIC,
    durable=True
)

order_created_publisher = broker.publisher(
    exchange=orders_events_exchange,
    routing_key=settings.ORDER_CREATED_ROUTING_KEY,
)


async def publish_order_created_event(payload: OrderCreatedEventPayload) -> None:
    await order_created_publisher.publish(payload)
