import os
import asyncio
from websockets.client import connect
import sys
from dotenv import load_dotenv

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
    async with connect(f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}") as websocket:
        group = asyncio.gather(async_input(websocket, *args), async_recv(websocket))
        await group


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
