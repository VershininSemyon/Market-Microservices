
import json
import logging

import aio_pika

from src.config import settings
from src.mail import (
    send_product_created_email,
    send_product_deleted_email,
    send_review_created_email,
    send_review_deleted_email,
    send_welcome_email,
)

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

    async def process_user_created(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=True):
            try:
                body = json.loads(message.body.decode("utf-8"))
                username = body.get("username")
                email = body.get("email")

                if not username or not email:
                    logger.warning(f"Некорректный формат сообщения: {body}")
                    return

                logger.info(f"Получено событие регистрации: {username} ({email})")
                await send_welcome_email(username=username, to_email=email)

            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON: {message.body}")
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при обработке сообщения: {e}")

    async def process_product_created(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=True):
            try:
                body = json.loads(message.body.decode("utf-8"))
                product_name = body.get("product_name")
                email = body.get("created_by")

                if not product_name or not email:
                    logger.warning(f"Некорректный формат сообщения: {body}")
                    return

                logger.info(f"Получено событие создания продукта: {product_name} ({email})")
                await send_product_created_email(product_name=product_name, to_email=email)

            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON: {message.body}")
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при обработке сообщения: {e}")

    async def process_product_deleted(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=True):
            try:
                body = json.loads(message.body.decode("utf-8"))
                product_name = body.get("product_name")
                email = body.get("deleted_by")

                if not product_name or not email:
                    logger.warning(f"Некорректный формат сообщения: {body}")
                    return

                logger.info(f"Получено событие удаления продукта: {product_name} ({email})")
                await send_product_deleted_email(product_name=product_name, to_email=email)

            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON: {message.body}")
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при обработке сообщения: {e}")

    async def process_review_created(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=True):
            try:
                body = json.loads(message.body.decode("utf-8"))
                product_id = body.get("product_id")
                email = body.get("user_email")

                if not product_id or not email:
                    logger.warning(f"Некорректный формат сообщения: {body}")
                    return

                logger.info(f"Получено событие создания отзыва для продукта {product_id} ({email})")
                await send_review_created_email(product_id=product_id, to_email=email)

            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON: {message.body}")
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при обработке сообщения: {e}")

    async def process_review_deleted(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=True):
            try:
                body = json.loads(message.body.decode("utf-8"))
                product_id = body.get("product_id")
                email = body.get("user_email")

                if not product_id or not email:
                    logger.warning(f"Некорректный формат сообщения: {body}")
                    return

                logger.info(f"Получено событие удаления отзыва для продукта {product_id} ({email})")
                await send_review_deleted_email(product_id=product_id, to_email=email)

            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON: {message.body}")
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при обработке сообщения: {e}")

    async def start_consuming(self) -> None:
        await self.connect()

        # Юзеры
        user_exchange = await self._channel.declare_exchange(
            name=settings.USER_EVENTS_EXCHANGE_NAME,
            type=aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        user_created_queue = await self._channel.declare_queue(
            name=settings.USER_CREATED_QUEUE_NAME,
            durable=True,
        )
        await user_created_queue.bind(
            exchange=user_exchange,
            routing_key=settings.USER_CREATED_ROUTING_KEY,
        )
        await user_created_queue.consume(self.process_user_created)

        # Продукты
        product_exchange = await self._channel.declare_exchange(
            name=settings.PRODUCTS_EVENTS_EXCHANGE_NAME,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        product_created_queue = await self._channel.declare_queue(
            name=settings.PRODUCT_CREATED_QUEUE_NAME,
            durable=True,
        )
        await product_created_queue.bind(
            exchange=product_exchange,
            routing_key=settings.PRODUCT_CREATED_ROUTING_KEY,
        )
        await product_created_queue.consume(self.process_product_created)

        product_deleted_queue = await self._channel.declare_queue(
            name=settings.PRODUCT_DELETED_QUEUE_NAME,
            durable=True,
        )
        await product_deleted_queue.bind(
            exchange=product_exchange,
            routing_key=settings.PRODUCT_DELETED_ROUTING_KEY,
        )
        await product_deleted_queue.consume(self.process_product_deleted)

        # Отзывы
        review_exchange = await self._channel.declare_exchange(
            name=settings.REVIEWS_EVENTS_EXCHANGE_NAME,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        review_created_queue = await self._channel.declare_queue(
            name=settings.REVIEW_CREATED_QUEUE_NAME,
            durable=True,
        )
        await review_created_queue.bind(
            exchange=review_exchange,
            routing_key=settings.REVIEW_CREATED_ROUTING_KEY,
        )
        await review_created_queue.consume(self.process_review_created)

        review_deleted_queue = await self._channel.declare_queue(
            name=settings.REVIEW_DELETED_QUEUE_NAME,
            durable=True,
        )
        await review_deleted_queue.bind(
            exchange=review_exchange,
            routing_key=settings.REVIEW_DELETED_ROUTING_KEY,
        )
        await review_deleted_queue.consume(self.process_review_deleted)
