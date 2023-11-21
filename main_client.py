import os
import sys
from dotenv import load_dotenv
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from websockets.client import connect
from tse_utils.models.instrument import Instrument, InstrumentIdentification
from tsetmc_pusher.client import TsetmcClient

load_dotenv()

WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST")
WEBSOCKET_PORT = os.getenv("WEBSOCKET_PORT")


async def async_input(websocket, *args):
    for arg in args:
        await websocket.send(arg)
    await asyncio.sleep(1)


async def async_recv(websocket):
    while True:
        message = await websocket.recv()
        print(f"Received: {message}")
        print("___________________________________")


async def main(*args):
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

    instruments = [
        Instrument(identification=x)
        for x in [
            InstrumentIdentification(isin="IRO1FOLD0001"),
            # InstrumentIdentification(isin="IRO1MSMI0001"),
            # InstrumentIdentification(isin="IRO1IKCO0001"),
        ]
    ]
    client = TsetmcClient(
        websocket_host=WEBSOCKET_HOST,
        websocket_port=WEBSOCKET_PORT,
        subscribed_instruments=instruments,
    )
    await client.infinite_operation()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
