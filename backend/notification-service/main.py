
import asyncio
import logging
import sys

from src.consumer import RabbitMQConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("main")


async def main():
    consumer = RabbitMQConsumer()
    try:
        await consumer.start_consuming()
        await asyncio.Future()
    finally:
        await consumer.close()
        logger.info("Соединения с RabbitMQ успешно закрыты.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Сервис остановлен пользователем.")
