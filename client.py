import asyncio
from websockets.client import connect
import sys


async def async_input(websocket, *args):
    # ym = input("Your message: ")
    for arg in args:
        await websocket.send(arg)
    await asyncio.sleep(1)


async def async_recv(websocket):
    while True:
        message = await websocket.recv()
        print(f"Received: {message}")
        print("___________________________________")


async def main(*args):
    async with connect("ws://localhost:8765") as websocket:
        group = asyncio.gather(async_input(websocket, *args), async_recv(websocket))
        await group


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
