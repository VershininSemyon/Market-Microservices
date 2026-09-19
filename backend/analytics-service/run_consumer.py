
import asyncio
import logging
import sys

from src.consumer import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("main")


async def main():
    logger.info("Запускается analytics consumer")
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
