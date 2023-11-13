import asyncio
from websockets.server import serve
from websockets.sync.client import ClientConnection
from websockets.exceptions import ConnectionClosedError


async def echo(websocket: ClientConnection):
    print(f"Connection opened to {websocket.id}")
    await websocket.send("Greetings!")
    try:
        async for message in websocket:
            print(f"Received: {message} | From: {websocket.id}")
            await websocket.send(message)
    except ConnectionClosedError:
        print(f"Connection closed to {websocket.id}")


async def main():
    async with serve(echo, "localhost", 8765):
        await asyncio.Future()


asyncio.run(main())
