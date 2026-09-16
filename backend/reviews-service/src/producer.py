
import json

import aio_pika

from src.config import settings


class RabbitMQProducer:
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

    async def publish_message(
        self,
        routing_key: str,
        message_body: dict
    ) -> None:
        await self.connect()

        exchange = await self._channel.declare_exchange(
            name=settings.REVIEWS_EVENTS_EXCHANGE_NAME,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        message = aio_pika.Message(
            body=json.dumps(message_body).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        await exchange.publish(
            message=message,
            routing_key=routing_key
        )


rabbitmq_producer = RabbitMQProducer()
