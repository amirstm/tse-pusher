"""
This module contains the websocket for TSETMC
"""
from dataclasses import dataclass
import logging
from typing import Callable
from threading import Lock
import websockets
from websockets.server import serve
from websockets.sync.client import ClientConnection
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from tsetmc_pusher.repository import MarketRealtimeData
from tsetmc_pusher.timing import sleep_until, MARKET_END_TIME


@dataclass
class InstrumentChannel:
    """Holds essential channels for each instrument"""

    isin: str = None
    trade_subscribers: set[ClientConnection] = None
    orderbook_subscribers: set[ClientConnection] = None
    clienttype_subscribers: set[ClientConnection] = None

    def __init__(self, isin: str):
        self.isin = isin
        self.trade_subscribers = set()
        self.orderbook_subscribers = set()
        self.clienttype_subscribers = set()


def subscribe_trade(client: ClientConnection, instrument_channel: InstrumentChannel):
    instrument_channel.trade_subscribers.add(client)


def subscribe_orderbook(
    client: ClientConnection, instrument_channel: InstrumentChannel
):
    instrument_channel.orderbook_subscribers.add(client)


def subscribe_clienttype(
    client: ClientConnection, instrument_channel: InstrumentChannel
):
    instrument_channel.clienttype_subscribers.add(client)


def subscribe_all(client: ClientConnection, instrument_channel: InstrumentChannel):
    subscribe_trade(client, instrument_channel)
    subscribe_orderbook(client, instrument_channel)
    subscribe_clienttype(client, instrument_channel)


def unsubscribe_trade(client: ClientConnection, instrument_channel: InstrumentChannel):
    try:
        instrument_channel.trade_subscribers.remove(client)
    except KeyError:
        pass


def unsubscribe_orderbook(
    client: ClientConnection, instrument_channel: InstrumentChannel
):
    try:
        instrument_channel.orderbook_subscribers.remove(client)
    except KeyError:
        pass


def unsubscribe_clienttype(
    client: ClientConnection, instrument_channel: InstrumentChannel
):
    try:
        instrument_channel.clienttype_subscribers.remove(client)
    except KeyError:
        pass


def unsubscribe_all(client: ClientConnection, instrument_channel: InstrumentChannel):
    unsubscribe_trade(client, instrument_channel)
    unsubscribe_orderbook(client, instrument_channel)
    unsubscribe_clienttype(client, instrument_channel)


class TsetmcWebsocket:
    """Holds the websocket for TSETMC"""

    _LOGGER = logging.getLogger(__name__)

    def __init__(self, market_realtime_data: MarketRealtimeData):
        self.market_realtime_data: MarketRealtimeData = market_realtime_data
        self.__channels: list[InstrumentChannel] = []
        self.__channels_lock = Lock()

    async def handle_connection(self, client: ClientConnection) -> None:
        """Handles the clients' connections"""
        self._LOGGER.info("Connection opened to [%s]", client.id)
        try:
            async for message in client:
                self._LOGGER.info(
                    "Receieved message [%s] from [%s]", message, client.id
                )
                self.handle_connection_message(client, message)
        except (ConnectionClosedError, ConnectionClosedOK):
            self._LOGGER.info("Connection closed to [%s]", client.id)
        finally:
            self.remove_from_channels(client)

    def remove_from_channels(self, client: ClientConnection) -> None:
        """Removes a client from all channels"""
        with self.__channels_lock:
            for channel in self.__channels:
                unsubscribe_all(client, channel)

    def handle_connection_message(self, client: ClientConnection, message: str) -> None:
        """
        Handles a single message from client
        Standard message format is: <Action>.<Channel>.<Isin1>,<Isin2>,...
        For instance: 1.trade.IRO1FOLD0001,IRO1IKCO0001
        """
        acceptable_actions = ["0", "1"]
        acceptable_channels = ["all", "trade", "orderbook", "clienttype"]
        message_parts = message.split(".")
        if len(message_parts) != 3:
            self._LOGGER.error("Message [%s] has unacceptable format.", message)
            return
        if message_parts[0] not in acceptable_actions:
            self._LOGGER.error("Action [%s] is not acceptable.", message_parts[0])
            return
        if message_parts[1] not in acceptable_channels:
            self._LOGGER.error("Channel [%s] is not acceptable.", message_parts[1])
            return
        isins = message_parts[2].split(",")
        fake_isin = next((x for x in isins if len(x) != 12), None)
        if fake_isin:
            self._LOGGER.error("Isin [%s] is not acceptable.", fake_isin)
            return
        channel_action_func = self.get_channel_action_func(
            message_parts[0], message_parts[1]
        )
        with self.__channels_lock:
            for isin in isins:
                channel = next((x for x in self.__channels), None)
                if not channel:
                    channel = InstrumentChannel(isin)
                    self.__channels.append(channel)
                channel_action_func(client, channel)

    def get_channel_action_func(
        self, action: str, channel: str
    ) -> Callable[[ClientConnection, InstrumentChannel], None]:
        """Returns the function for handling the actions"""
        return_values = {
            "1": {
                "all": subscribe_all,
                "trade": subscribe_trade,
                "orderbook": subscribe_orderbook,
                "clienttype": subscribe_clienttype,
            },
            "0": {
                "all": unsubscribe_all,
                "trade": unsubscribe_trade,
                "orderbook": unsubscribe_orderbook,
                "clienttype": unsubscribe_clienttype,
            },
        }
        return return_values[action][channel]

    async def serve_websocket(self):
        """Serves the websocket for the project"""
        self._LOGGER.info("Serving has started.")
        async with serve(self.handle_connection, "localhost", 8765):
            await sleep_until(MARKET_END_TIME)
        self._LOGGER.info("Serving has ended.")
