"""
This module contains the necessary codes for the TSETMC pusher's client.
"""
import json
import logging
from websockets import client
from websockets.sync.client import ClientConnection
from tse_utils.models.instrument import Instrument


class TsetmcClient:
    """
The class used for connecting to the TSETMC pusher websocket \
and subscribe to its realtime data
    """

    _LOGGER = logging.getLogger(__name__)

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
        """Listens to websocket updates"""
        while True:
            message = await self.websocket.recv()
            self._LOGGER.debug("Client received: %s", message)
            self.process_message(message=message)

    def process_message(self, message: str):
        """Processes a new message received from websocket"""
        message_js = json.loads(message)
        for isin, channels in message_js.items():
            instrument = next(
                x for x in self.subscribed_instruments if x.identification.isin == isin
            )
            for channel, data in channels.items():
                match channel:
                    case "thresholds":
                        pass
                    case "trade":
                        pass
                    case "orderbook":
                        pass
                    case "clienttype":
                        pass
                    case _:
                        self._LOGGER.fatal("Unknown message channel: %s", channel)

    async def subscribe(self) -> None:
        """Subscribe to the channels for the appointed instruemtns"""
        self._LOGGER.info(
            "Client is subscribing to data for %d instruments.",
            len(self.subscribed_instruments),
        )
        isins = ",".join([x.identification.isin for x in self.subscribed_instruments])
        await self.websocket.send(f"1.all.{isins}")

    async def operate(self) -> None:
        """Start connecting to the websocket and listening for updates"""
        self._LOGGER.info("Client is starting its operation.")
        async with client.connect(
            f"ws://{self.websocket_host}:{self.websocket_port}"
        ) as self.websocket:
            await self.subscribe()
            await self.listen()
