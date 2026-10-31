
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

    if not events:
        return

    processed_event_ids = []

    for event in events:
        try:
            payload = OrderCreatedEventPayload.model_validate(event.event_payload)
            await publish_order_created_event(payload)

            processed_event_ids.append(event.id)
            logger.info(f"Событие {event.id} успешно опубликовано")
        except Exception as e:
            logger.error(f"Ошибка при публикации события {event.id}: {e}")

    if processed_event_ids:
        async with uow:
            await uow.outbox_repo.delete_outbox_events(processed_event_ids)
            await uow.commit()
        logger.info(f"Удалено {len(processed_event_ids)} обработанных событий из outbox")


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
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(main())
