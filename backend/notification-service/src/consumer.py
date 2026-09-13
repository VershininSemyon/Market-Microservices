
import json
import logging

import aio_pika
from src.config import settings
from src.mail import send_welcome_email

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

    async def process_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process():
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

    async def start_consuming(self) -> None:
        await self.connect()

        exchange = await self._channel.declare_exchange(
            name=settings.USER_EVENTS_EXCHANGE_NAME,
            type=aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        queue = await self._channel.declare_queue(
            name=settings.NOTIFICATION_QUEUE_NAME,
            durable=True,
        )

        await queue.bind(
            exchange=exchange,
            routing_key=settings.USER_CREATED_ROUTING_KEY,
        )

        await queue.consume(self.process_message)
