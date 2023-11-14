"""
This module contains the websocket for TSETMC
"""
import asyncio
from websockets.server import serve
from websockets.sync.client import ClientConnection
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from tsetmc_pusher.repository import MarketRealtimeData


class TsetmcWebsocket:
    """Holds the websocket for TSETMC"""

    def __init__(self, market_realtime_data: MarketRealtimeData):
        self.market_realtime_data: MarketRealtimeData = market_realtime_data

    async def handle_connection(self, websocket: ClientConnection):
        """Handles the clients' connections"""
        print(f"Connection opened to {websocket.id}")
        await websocket.send("Greetings!")
        try:
            async for message in websocket:
                print(f"Received: {message} | From: {websocket.id}")
                await websocket.send(message)
        except (ConnectionClosedError, ConnectionClosedOK):
            print(f"Connection closed to {websocket.id}")

    async def serve(self):
        """Serves the websocket for the project"""
        async with serve(self.handle_connection, "localhost", 8765):
            await asyncio.Future()
