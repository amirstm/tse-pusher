"""Manual test for telegram_task library"""
import os
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from tsetmc_pusher.operation import TsetmcOperator


async def main():
    """Manually testing the pusher"""
    logger = logging.getLogger("tsetmc_pusher")
    formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s: %(message)s")
    logger.setLevel(logging.INFO)
    log_file_path = "logs/log_"
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=log_file_path, when="midnight", backupCount=30
    )
    file_handler.suffix = "%Y_%m_%d.log"
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    operator = TsetmcOperator()
    await operator.perform_daily()


if __name__ == "__main__":
    asyncio.new_event_loop().run_until_complete(main())
