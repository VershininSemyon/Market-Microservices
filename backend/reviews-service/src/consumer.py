
import json
import logging

import aio_pika

from src.config import settings
from src.database import async_session_factory
from src.redis_manager import redis_manager
from src.services import ReviewService
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

        await redis_manager.connect()

    async def close(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

        await redis_manager.disconnect()

    async def process_product_deleted(self, message: aio_pika.IncomingMessage) -> None:
        try:
            body = json.loads(message.body.decode("utf-8"))
            product_id = body.get("product_id")

            if not product_id:
                logger.warning(f"Некорректный формат сообщения (нет product_id): {body}")
                await message.nack(requeue=False)
                return

            logger.info(f"Получено событие удаления продукта {product_id}")

            uow = UnitOfWork(async_session_factory)
            review_service = ReviewService(uow)

            async with uow:
                await uow.review_repo.delete_product_reviews(product_id)
                await uow.commit()

            await review_service.invalidate_review_list_cache(product_id)
            await message.ack()

        except json.JSONDecodeError:
            logger.error(f"Ошибка декодирования JSON: {message.body}")
            await message.nack(requeue=False)
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обработке сообщения: {e}")
            await message.nack(requeue=False)

    async def process_dlq(self, message: aio_pika.IncomingMessage) -> None:
        try:
            body_str = message.body.decode("utf-8")
            try:
                parsed_body = json.loads(body_str)
            except json.JSONDecodeError:
                parsed_body = body_str

            headers = message.headers or {}
            death_exchange = headers.get("x-first-death-exchange")
            death_queue = headers.get("x-first-death-queue")

            logger.error(
                f"DLQ: Сообщение из обменника '{death_exchange}', "
                f"очереди '{death_queue}'."
                f"Тело: {parsed_body}"
            )

            await message.ack()
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке сообщения из DLQ: {e}")
            await message.nack(requeue=False)

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
            arguments={
                "x-dead-letter-exchange": settings.DLX_EXCHANGE_NAME,
            }
        )
        await product_deleted_queue.bind(
            exchange=product_exchange,
            routing_key=settings.PRODUCT_DELETED_ROUTING_KEY,
        )
        await product_deleted_queue.consume(self.process_product_deleted)

        # DLX + DLQ
        dlx = await self._channel.declare_exchange(
            name=settings.DLX_EXCHANGE_NAME,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        dlq = await self._channel.declare_queue(
            name=settings.DLQ_NAME,
            durable=True,
        )

        await dlq.bind(
            exchange=dlx,
            routing_key="#"
        )

        await dlq.consume(self.process_dlq)


rabbitmq_consumer = RabbitMQConsumer()
