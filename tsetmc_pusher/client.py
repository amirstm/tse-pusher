"""
This module contains the necessary codes for the TSETMC pusher's client.
"""
from websockets import client
from websockets.sync.client import ClientConnection
from tse_utils.models.instrument import Instrument


class TsetmcClient:
    """
The class used for connecting to the TSETMC pusher websocket \
and subscribe to its realtime data
    """

    def __init__(
        self,
        websocket_host: str,
        websocket_port: int,
        subscribed_instruments: list[Instrument],
    ):
        self.websocket_host: str = websocket_host
        self.websocket_port: int = websocket_port
        self.websocket: ClientConnection = None
        self.subscribed_instruments: list[Instrument] = subscribed_instruments

    async def listen(self):
        while True:
            message = await self.websocket.recv()
            print(f"Received: {message}")
            print("___________________________________")

    async def subscribe(self):
        isins = ",".join([x.identification.isin for x in self.subscribed_instruments])
        await self.websocket.send(f"1.all.{isins}")

    async def operate(self):
        """Start connecting to the websocket and listening for updates"""
        async with client.connect(
            f"ws://{self.websocket_host}:{self.websocket_port}"
        ) as self.websocket:
            await self.subscribe()
            await self.listen()
