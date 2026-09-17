
import json
import logging

import aio_pika

from src.config import settings
from src.database import async_session_factory
from src.unitofwork import UnitOfWork

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    def __init__(self, amqp_url: str = settings.amqp_url):
        self._amqp_url = amqp_url
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None

    async def connect(self) -> None:
        if not self._connection or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self._amqp_url)
            self._channel = await self._connection.channel()

    async def close(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

    async def process_product_deleted(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=True):
            try:
                body = json.loads(message.body.decode("utf-8"))
                product_id = body.get("product_id")

                if not product_id:
                    logger.warning(f"Некорректный формат сообщения: {body}")
                    return

                logger.info(f"Получено событие удаления продукта {product_id}")

                uow = UnitOfWork(async_session_factory)
                async with uow:
                    await uow.review_repo.delete_product_reviews(product_id)
                    await uow.commit()

            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON: {message.body}")
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при обработке сообщения: {e}")

    async def start_consuming(self) -> None:
        await self.connect()

        # Продукты
        product_exchange = await self._channel.declare_exchange(
            name=settings.PRODUCTS_EVENTS_EXCHANGE_NAME,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        product_deleted_queue = await self._channel.declare_queue(
            name=settings.PRODUCT_DELETED_QUEUE_NAME,
            durable=True,
        )
        await product_deleted_queue.bind(
            exchange=product_exchange,
            routing_key=settings.PRODUCT_DELETED_ROUTING_KEY,
        )
        await product_deleted_queue.consume(self.process_product_deleted)


rabbitmq_consumer = RabbitMQConsumer()
