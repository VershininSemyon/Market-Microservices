
import asyncio
import logging

from src.database import async_session_factory
from src.producer import OrderCreatedEventPayload, broker, publish_order_created_event
from src.unitofwork import UnitOfWork

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OutboxScheduler")


async def process_outbox():
    uow = UnitOfWork(async_session_factory)

    async with uow:
        events = await uow.outbox_repo.get_last_outbox_events(10)

        tasks = [
            publish_order_created_event(
                OrderCreatedEventPayload.model_validate(event.event_payload)
            )
            for event in events
        ]

        await asyncio.gather(*tasks)


async def main():
    logger.info("Подключение к RabbitMQ")
    await broker.start()
    logger.info("Outbox Scheduler запущен и ожидает задач")

    try:
        while True:
            await process_outbox()
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        pass
    finally:
        await broker.close()


if __name__ == "__main__":
    asyncio.run(main())
