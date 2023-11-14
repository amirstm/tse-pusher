"""
This module contains the websocket for TSETMC
"""
from threading import Lock
import websockets
from websockets.server import serve
from websockets.sync.client import ClientConnection
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from tsetmc_pusher.repository import MarketRealtimeData
from tsetmc_pusher.timing import sleep_until, MARKET_END_TIME


class TsetmcWebsocket:
    """Holds the websocket for TSETMC"""

    def __init__(self, market_realtime_data: MarketRealtimeData):
        self.market_realtime_data: MarketRealtimeData = market_realtime_data
        self.__subscriptions: dict[ClientConnection, list[str]] = {}
        self.__subscriptions_lock: Lock = Lock()

    async def handle_connection(self, client: ClientConnection):
        """Handles the clients' connections"""
        print(f"Connection opened to {client.id}")
        self.add_subscription_key(client)
        websockets.broadcast(self.__subscriptions.keys(), f"Greetings to {client.id}!")
        try:
            async for message in client:
                print(f"Received: {message} | From: {client.id}")
                await client.send(message)
        except (ConnectionClosedError, ConnectionClosedOK):
            print(f"Connection closed to {client.id}")
        finally:
            self.del_subscription_key(client)

    def add_subscription_key(self, client: ClientConnection):
        """Adds newly connected websocket as a key to the subscriptions"""
        with self.__subscriptions_lock:
            self.__subscriptions[client] = []

    def del_subscription_key(self, client: ClientConnection):
        """Deletes websocket from the keys of the sub scriptions"""
        with self.__subscriptions_lock:
            self.__subscriptions.pop(client)

    async def serve_websocket(self):
        """Serves the websocket for the project"""
        async with serve(self.handle_connection, "localhost", 8765):
            await sleep_until(MARKET_END_TIME)
