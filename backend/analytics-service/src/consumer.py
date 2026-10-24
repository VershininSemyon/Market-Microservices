
import logging

from faststream import FastStream, Logger
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitMessage, RabbitQueue

from src.config import settings
from src.database import async_session_factory
from src.enums import EntityTypeEnum, EventTypeEnum
from src.schemas import EventDateMessageSchema
from src.services import AnalyticsService
from src.unitofwork import UnitOfWork

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


uow = UnitOfWork(async_session_factory)
analytics_service = AnalyticsService(uow)


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
    exchange=user_exchange,
)
async def process_user_created(
    msg: EventDateMessageSchema,
    logger: Logger,
) -> None:
    logger.info("Получено событие регистрации пользователя")
    await analytics_service.add_analytics(
        entity_type=EntityTypeEnum.USER,
        event_type=EventTypeEnum.CREATED,
        day=msg.event_date
    )


@broker.subscriber(
    queue=create_queue(settings.USER_DELETED_QUEUE_NAME, settings.USER_DELETED_ROUTING_KEY),
    exchange=user_exchange,
)
async def process_user_deleted(
    msg: EventDateMessageSchema,
    logger: Logger,
) -> None:
    logger.info("Получено событие удаления аккаунта")
    await analytics_service.add_analytics(
        entity_type=EntityTypeEnum.USER,
        event_type=EventTypeEnum.DELETED,
        day=msg.event_date
    )


@broker.subscriber(
    queue=create_queue(settings.PRODUCT_CREATED_QUEUE_NAME, settings.PRODUCT_CREATED_ROUTING_KEY),
    exchange=products_exchange,
)
async def process_product_created(
    msg: EventDateMessageSchema,
    logger: Logger,
) -> None:
    logger.info("Получено событие создания продукта")
    await analytics_service.add_analytics(
        entity_type=EntityTypeEnum.PRODUCT,
        event_type=EventTypeEnum.CREATED,
        day=msg.event_date
    )


@broker.subscriber(
    queue=create_queue(settings.PRODUCT_DELETED_QUEUE_NAME, settings.PRODUCT_DELETED_ROUTING_KEY),
    exchange=products_exchange,
)
async def process_product_deleted(
    msg: EventDateMessageSchema,
    logger: Logger,
) -> None:
    logger.info("Получено событие удаления продукта")
    await analytics_service.add_analytics(
        entity_type=EntityTypeEnum.PRODUCT,
        event_type=EventTypeEnum.DELETED,
        day=msg.event_date
    )


@broker.subscriber(
    queue=create_queue(settings.REVIEW_CREATED_QUEUE_NAME, settings.REVIEW_CREATED_ROUTING_KEY),
    exchange=reviews_exchange,
)
async def process_review_created(
    msg: EventDateMessageSchema,
    logger: Logger,
) -> None:
    logger.info("Получено событие создания отзыва для продукта")
    await analytics_service.add_analytics(
        entity_type=EntityTypeEnum.REVIEW,
        event_type=EventTypeEnum.CREATED,
        day=msg.event_date
    )


@broker.subscriber(
    queue=create_queue(settings.REVIEW_DELETED_QUEUE_NAME, settings.REVIEW_DELETED_ROUTING_KEY),
    exchange=reviews_exchange,
)
async def process_review_deleted(
    msg: EventDateMessageSchema,
    logger: Logger,
) -> None:
    logger.info("Получено событие удаления отзыва для продукта")
    await analytics_service.add_analytics(
        entity_type=EntityTypeEnum.REVIEW,
        event_type=EventTypeEnum.DELETED,
        day=msg.event_date
    )
