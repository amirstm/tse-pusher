import asyncio
from websockets.client import connect


async def async_input(websocket):
    while True:
        ym = input("Your message: ")
        await websocket.send(ym)
        await asyncio.sleep(1)


async def async_recv(websocket):
    while True:
        message = await websocket.recv()
        print(f"Received: {message} | From: {websocket.id}")


async def main():
    async with connect("ws://localhost:8765") as websocket:
        print(type(websocket))
        group = asyncio.gather(async_input(websocket), async_recv(websocket))
        await group


asyncio.run(main())
