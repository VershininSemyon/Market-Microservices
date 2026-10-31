
import asyncio
import json
import logging

import aio_pika

from src.config import settings
from src.database import async_session_factory
from src.redis_cache_backend import redis_cache
from src.redis_manager import redis_manager
from src.services import ProductService
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

    async def _update_product_data(
        self,
        uow: UnitOfWork,
        product_service: ProductService,
        product_id: str,
        quantity: int
    ) -> None:
        async with uow:
            await uow.product_repo.change_product_quantity(product_id, -quantity)
            await uow.commit()

        await product_service.invalidate_products_cache(product_id)

    async def process_order_created(self, message: aio_pika.IncomingMessage) -> None:
        try:
            body = json.loads(message.body.decode("utf-8"))
            event_id = body.get("event_id")

            if not event_id:
                logger.warning(f"Некорректный формат сообщения (нет event_id): {body}")
                await message.nack(requeue=False)
                return

            event_cache = await redis_cache.get_value(f"events:{event_id}")

            if event_cache == "done":
                await message.ack()
                return

            products = body.get("products")

            if not products:
                logger.warning(f"Некорректный формат сообщения (нет products): {body}")
                await message.nack(requeue=False)
                return

            logger.info(f"Получено событие создания заказа с продуктами: {products}")

            uow = UnitOfWork(async_session_factory)
            product_service = ProductService(uow)
            tasks = []

            for product in products:
                if "id" not in product or "quantity" not in product:
                    logger.warning(f"Некорректный формат продукта: {product}")
                    await message.nack(requeue=False)
                    return

                tasks.append(
                    self._update_product_data(
                        uow,
                        product_service,
                        product["id"],
                        product["quantity"]
                    )
                )

            await asyncio.gather(*tasks)
            await redis_cache.set_value(f"events:{event_id}", "done")
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

        # Заказы
        order_exchange = await self._channel.declare_exchange(
            name=settings.ORDERS_EVENTS_EXCHANGE_NAME,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        order_created_queue = await self._channel.declare_queue(
            name=settings.ORDER_CREATED_QUEUE_NAME,
            durable=True,
            arguments={
                "x-dead-letter-exchange": settings.DLX_EXCHANGE_NAME,
            }
        )
        await order_created_queue.bind(
            exchange=order_exchange,
            routing_key=settings.ORDER_CREATED_ROUTING_KEY,
        )
        await order_created_queue.consume(self.process_order_created)

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
