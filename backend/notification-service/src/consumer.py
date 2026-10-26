
import logging

from faststream import FastStream, Logger
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitMessage, RabbitQueue

from src.config import settings
from src.mail import (
    send_account_deleted_email,
    send_order_created_email,
    send_product_created_email,
    send_product_deleted_email,
    send_review_created_email,
    send_review_deleted_email,
    send_welcome_email,
)
from src.schemas import (
    OrderCreatedMessage,
    ProductCreatedMessage,
    ProductDeletedMessage,
    ReviewMessage,
    UserCreatedMessage,
    UserDeletedMessage,
)

logger = logging.getLogger(__name__)

broker = RabbitBroker(url=settings.amqp_url, logger=logger)
app = FastStream(broker)

user_exchange = RabbitExchange(
    name=settings.USER_EVENTS_EXCHANGE_NAME,
    type=ExchangeType.TOPIC,
    durable=True
)

products_exchange = RabbitExchange(
    name=settings.PRODUCTS_EVENTS_EXCHANGE_NAME,
    type=ExchangeType.TOPIC,
    durable=True
)

reviews_exchange = RabbitExchange(
    name=settings.REVIEWS_EVENTS_EXCHANGE_NAME,
    type=ExchangeType.TOPIC,
    durable=True
)

order_exchange = RabbitExchange(
    name=settings.ORDERS_EVENTS_EXCHANGE_NAME,
    type=ExchangeType.TOPIC,
    durable=True
)

dlx_exchange = RabbitExchange(
    name=settings.DLX_EXCHANGE_NAME,
    type=ExchangeType.TOPIC,
    durable=True
)

dlq = RabbitQueue(
    name=settings.DLQ_NAME,
    durable=True,
    routing_key="#"
)


def create_queue(name: str, routing_key: str) -> RabbitQueue:
    return RabbitQueue(
        name=name,
        routing_key=routing_key,
        durable=True,
        arguments={
            "x-dead-letter-exchange": settings.DLX_EXCHANGE_NAME,
        }
    )


@broker.subscriber(
    queue=dlq,
    exchange=dlx_exchange
)
async def handle_dlq(
    body: dict,
    logger: Logger,
    message: RabbitMessage
) -> None:
    msg_exchange = message.headers.get("x-first-death-exchange")
    logger.error(f"DLQ Из обменника: {msg_exchange}, тело: {body}")


@broker.subscriber(
    queue=create_queue(settings.USER_CREATED_QUEUE_NAME, settings.USER_CREATED_ROUTING_KEY),
    exchange=user_exchange
)
async def process_user_created(
    msg: UserCreatedMessage,
    logger: Logger,
) -> None:
    logger.info(f"Получено событие регистрации: {msg.username} ({msg.email})")
    await send_welcome_email(username=msg.username, to_email=msg.email)


@broker.subscriber(
    queue=create_queue(settings.USER_DELETED_QUEUE_NAME, settings.USER_DELETED_ROUTING_KEY),
    exchange=user_exchange,
)
async def process_user_deleted(
    msg: UserDeletedMessage,
    logger: Logger,
) -> None:
    logger.info(f"Получено событие удаления аккаунта: {msg.email}")
    await send_account_deleted_email(to_email=msg.email)


@broker.subscriber(
    queue=create_queue(settings.PRODUCT_CREATED_QUEUE_NAME, settings.PRODUCT_CREATED_ROUTING_KEY),
    exchange=products_exchange,
)
async def process_product_created(
    msg: ProductCreatedMessage,
    logger: Logger,
) -> None:
    logger.info(f"Получено событие создания продукта: {msg.product_name} ({msg.created_by})")
    await send_product_created_email(product_name=msg.product_name, to_email=msg.created_by)


@broker.subscriber(
    queue=create_queue(settings.PRODUCT_DELETED_QUEUE_NAME, settings.PRODUCT_DELETED_ROUTING_KEY),
    exchange=products_exchange,
)
async def process_product_deleted(
    msg: ProductDeletedMessage,
    logger: Logger,
) -> None:
    logger.info(f"Получено событие удаления продукта: {msg.product_name} ({msg.deleted_by})")
    await send_product_deleted_email(product_name=msg.product_name, to_email=msg.deleted_by)


@broker.subscriber(
    queue=create_queue(settings.REVIEW_CREATED_QUEUE_NAME, settings.REVIEW_CREATED_ROUTING_KEY),
    exchange=reviews_exchange,
)
async def process_review_created(
    msg: ReviewMessage,
    logger: Logger,
) -> None:
    logger.info(f"Получено событие создания отзыва для продукта {msg.product_id} ({msg.user_email})")
    await send_review_created_email(product_id=msg.product_id, to_email=msg.user_email)


@broker.subscriber(
    queue=create_queue(settings.REVIEW_DELETED_QUEUE_NAME, settings.REVIEW_DELETED_ROUTING_KEY),
    exchange=reviews_exchange,
)
async def process_review_deleted(
    msg: ReviewMessage,
    logger: Logger,
) -> None:
    logger.info(f"Получено событие удаления отзыва для продукта {msg.product_id} ({msg.user_email})")
    await send_review_deleted_email(product_id=msg.product_id, to_email=msg.user_email)


@broker.subscriber(
    queue=create_queue(settings.ORDER_CREATED_QUEUE_NAME, settings.ORDER_CREATED_ROUTING_KEY),
    exchange=order_exchange,
)
async def process_order_created(
    msg: OrderCreatedMessage,
    logger: Logger,
) -> None:
    logger.info(f"Получено событие создания заказа: {msg.total_price} ({msg.user_email})")
    await send_order_created_email(total_price=msg.total_price, total_amount=msg.total_amount, to_email=msg.user_email)
