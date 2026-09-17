
import asyncio
import logging

from src.consumer import rabbitmq_consumer

logger = logging.getLogger(__name__)


async def main():
    await rabbitmq_consumer.connect()
    await rabbitmq_consumer.start_consuming()
    logger.info("Консьюмер запущен")

    try:
        await asyncio.Future()
    finally:
        await rabbitmq_consumer.close()


if __name__ == "__main__":
    asyncio.run(main())
