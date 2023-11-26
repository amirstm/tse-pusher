"""Sample executable python code for client side"""

import os
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
from tse_utils.models.instrument import Instrument, InstrumentIdentification
from tsetmc_pusher.client import TsetmcClient

load_dotenv()

WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST")
WEBSOCKET_PORT = os.getenv("WEBSOCKET_PORT")


async def main():
    """Main asynchronous executable method"""
    logger = logging.getLogger("tsetmc_pusher")
    formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s: %(message)s")
    logger.setLevel(logging.DEBUG)
    log_file_path = "logs/log_"
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=log_file_path, when="midnight", backupCount=30
    )
    file_handler.suffix = "%Y_%m_%d.log"
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    global_subscription = True
    instruments = (
        None
        if global_subscription
        else [
            Instrument(identification=x)
            for x in [
                InstrumentIdentification(isin="IRO1FOLD0001"),
                # InstrumentIdentification(isin="IRO1MSMI0001"),
                # InstrumentIdentification(isin="IRO1IKCO0001"),
            ]
        ]
    )
    client = TsetmcClient(
        websocket_host=WEBSOCKET_HOST,
        websocket_port=WEBSOCKET_PORT,
        subscribed_instruments=instruments,
        global_subscriber=global_subscription,
    )
    await client.infinite_operation()


if __name__ == "__main__":
    asyncio.run(main())
