"""
This module contains the websocket for TSETMC
"""
import asyncio
from websockets.server import serve
from websockets.sync.client import ClientConnection
from websockets.exceptions import ConnectionClosedError
from tsetmc_pusher.repository import MarketRealtimeData


class TsetmcWebsocket:
    """Holds the websocket for TSETMC"""

    def __init__(self, market_realtime_data: MarketRealtimeData):
        self.market_realtime_data: MarketRealtimeData = market_realtime_data

    async def echo(self, websocket: ClientConnection):
        print(f"Connection opened to {websocket.id}")
        await websocket.send("Greetings!")
        try:
            async for message in websocket:
                print(f"Received: {message} | From: {websocket.id}")
                await websocket.send(message)
        except ConnectionClosedError:
            print(f"Connection closed to {websocket.id}")

    async def start(self):
        async with serve(self.echo, "localhost", 8765):
            await asyncio.Future()
