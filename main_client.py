import os
import sys
from dotenv import load_dotenv
import asyncio
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
    # async with connect(f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}") as websocket:
    #     group = asyncio.gather(async_input(websocket, *args), async_recv(websocket))
    #     await group
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
    await client.operate()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
