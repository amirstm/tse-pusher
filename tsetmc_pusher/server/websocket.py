"""
This module contains the websocket for TSETMC
"""
import asyncio
import json
from dataclasses import dataclass
import logging
from typing import Callable, Awaitable
from threading import Lock
from websockets.server import serve
from websockets.sync.client import ClientConnection
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from tse_utils.models.instrument import Instrument
from tsetmc_pusher.server.repository import MarketRealtimeData
from tsetmc_pusher.server.timing import sleep_until, MARKET_END_TIME


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

    def __repr__(self) -> str:
        return f"{self.isin}: {[x.id for x in self.orderbook_subscribers]}"


def subscribe_trade(client: ClientConnection, instrument_channel: InstrumentChannel):
    """Subscribe to instrument's trade data"""
    instrument_channel.trade_subscribers.add(client)


def subscribe_orderbook(
    client: ClientConnection, instrument_channel: InstrumentChannel
):
    """Subscribe to instrument's orderbook data"""
    instrument_channel.orderbook_subscribers.add(client)


def subscribe_clienttype(
    client: ClientConnection, instrument_channel: InstrumentChannel
):
    """Subscribe to instrument's clienttype data"""
    instrument_channel.clienttype_subscribers.add(client)


def subscribe_all(client: ClientConnection, instrument_channel: InstrumentChannel):
    """Subscribe to all instrument's data"""
    subscribe_trade(client, instrument_channel)
    subscribe_orderbook(client, instrument_channel)
    subscribe_clienttype(client, instrument_channel)


def unsubscribe_trade(client: ClientConnection, instrument_channel: InstrumentChannel):
    """Unsubscribe from instrument's trade data"""
    try:
        instrument_channel.trade_subscribers.remove(client)
    except KeyError:
        pass


def unsubscribe_orderbook(
    client: ClientConnection, instrument_channel: InstrumentChannel
):
    """Unsubscribe from instrument's orderbook data"""
    try:
        instrument_channel.orderbook_subscribers.remove(client)
    except KeyError:
        pass


def unsubscribe_clienttype(
    client: ClientConnection, instrument_channel: InstrumentChannel
):
    """Unsubscribe from instrument's clienttype data"""
    try:
        instrument_channel.clienttype_subscribers.remove(client)
    except KeyError:
        pass


def unsubscribe_all(client: ClientConnection, instrument_channel: InstrumentChannel):
    """Unsubscribe from all instrument's data"""
    unsubscribe_trade(client, instrument_channel)
    unsubscribe_orderbook(client, instrument_channel)
    unsubscribe_clienttype(client, instrument_channel)


def instrument_data_trade(instrument: Instrument) -> list:
    """Convert instrument's trade data for websocket transfer"""
    ltd = instrument.intraday_trade_candle.last_trade_datetime
    ltd_display = f"{ltd.year}/{ltd.month:02}/{ltd.day:02} \
{ltd.hour:02}:{ltd.minute:02}:{ltd.second:02}"
    return {
        "trade": [
            instrument.intraday_trade_candle.close_price,
            instrument.intraday_trade_candle.last_price,
            ltd_display,
            instrument.intraday_trade_candle.max_price,
            instrument.intraday_trade_candle.min_price,
            instrument.intraday_trade_candle.open_price,
            instrument.intraday_trade_candle.previous_price,
            instrument.intraday_trade_candle.trade_num,
            instrument.intraday_trade_candle.trade_value,
            instrument.intraday_trade_candle.trade_volume,
        ]
    }


def instrument_data_orderbook_specific_rows(
    instrument: Instrument, rows: list[int] = None
) -> list:
    """Convert instrument's orderbook data for websocket transfer"""
    return {
        "orderbook": [
            [
                rn,
                x.demand.num,
                x.demand.price,
                x.demand.volume,
                x.supply.num,
                x.supply.price,
                x.supply.volume,
            ]
            for rn, x in enumerate(instrument.orderbook.rows)
            if rn in rows
        ]
    }


def instrument_data_orderbook(instrument: Instrument) -> list:
    """Convert instrument's orderbook data for websocket transfer"""
    return {
        "orderbook": [
            [
                rn,
                x.demand.num,
                x.demand.price,
                x.demand.volume,
                x.supply.num,
                x.supply.price,
                x.supply.volume,
            ]
            for rn, x in enumerate(instrument.orderbook.rows)
        ]
    }


def instrument_data_clienttype(instrument: Instrument) -> list[int]:
    """Convert instrument's clienttype data for websocket transfer"""
    return {
        "clienttype": [
            instrument.client_type.legal.buy.num,
            instrument.client_type.legal.buy.volume,
            instrument.client_type.legal.sell.num,
            instrument.client_type.legal.sell.volume,
            instrument.client_type.natural.buy.num,
            instrument.client_type.natural.buy.volume,
            instrument.client_type.natural.sell.num,
            instrument.client_type.natural.sell.volume,
        ]
    }


def instrument_data_thresholds(instrument: Instrument) -> list[int]:
    """Convert instrument's price thresholds data for websocket transfer"""
    return {
        "thresholds": [
            instrument.order_limitations.max_price,
            instrument.order_limitations.min_price,
        ]
    }


def instrument_data_all(instrument: Instrument) -> dict[str, list]:
    """Convert all instrument's data for websocket transfer"""
    return (
        instrument_data_thresholds(instrument)
        | instrument_data_trade(instrument)
        | instrument_data_orderbook(instrument)
        | instrument_data_clienttype(instrument)
    )


class TsetmcWebsocket:
    """Holds the websocket for TSETMC"""

    _LOGGER = logging.getLogger(__name__)

    def __init__(
        self,
        market_realtime_data: MarketRealtimeData,
        websocket_host: str,
        websocket_port: int,
    ):
        self.market_realtime_data: MarketRealtimeData = market_realtime_data
        self.websocket_host: str = websocket_host
        self.websocket_port: int = websocket_port
        self.__channels: list[InstrumentChannel] = []
        self.__channels_lock = Lock()
        self.set_market_realtime_data_pushers()

    def set_market_realtime_data_pushers(self) -> None:
        """Sets the pusher methods for market realtime data"""
        self.market_realtime_data.pusher_trade_data = self.pusher_trade_data
        self.market_realtime_data.pusher_orderbook_data = self.pusher_orderbook_data
        self.market_realtime_data.pusher_clienttype_data = self.pusher_clienttype_data

    async def pusher_trade_data(
        self, instruments: list[Instrument]
    ) -> Callable[[list[Instrument]], Awaitable[None]]:
        """Returns the pusher_trade_data to override in repo"""
        for instrument in instruments:
            with self.__channels_lock:
                channel = next(
                    (
                        x
                        for x in self.__channels
                        if x.isin == instrument.identification.isin
                    ),
                    None,
                )
                if channel and channel.trade_subscribers:
                    await self.broadcast(
                        channel.trade_subscribers,
                        json.dumps({channel.isin: instrument_data_trade(instrument)}),
                    )

    async def pusher_orderbook_data(
        self, instruments: list[Instrument]
    ) -> Callable[[list[tuple[Instrument, list[int]]]], Awaitable[None]]:
        """Returns the pusher_orderbook_data to override in repo"""
        for instrument, rows in instruments:
            with self.__channels_lock:
                channel = next(
                    (
                        x
                        for x in self.__channels
                        if x.isin == instrument.identification.isin
                    ),
                    None,
                )
                if channel and channel.orderbook_subscribers:
                    await self.broadcast(
                        channel.orderbook_subscribers,
                        json.dumps(
                            {
                                channel.isin: instrument_data_orderbook_specific_rows(
                                    instrument, rows
                                )
                            }
                        ),
                    )

    async def pusher_clienttype_data(
        self, instruments: list[Instrument]
    ) -> Callable[[list[Instrument]], Awaitable[None]]:
        """Returns the pusher_clienttype_data to override in repo"""
        for instrument in instruments:
            with self.__channels_lock:
                channel = next(
                    (
                        x
                        for x in self.__channels
                        if x.isin == instrument.identification.isin
                    ),
                    None,
                )
                if channel and channel.clienttype_subscribers:
                    await self.broadcast(
                        channel.clienttype_subscribers,
                        json.dumps(
                            {channel.isin: instrument_data_clienttype(instrument)}
                        ),
                    )

    @classmethod
    async def broadcast(cls, clients: list[ClientConnection], message: str) -> None:
        """Broadcast a message to a bunch of users"""
        group = asyncio.gather(*[client.send(message) for client in clients])
        await asyncio.wait_for(group, timeout=None)

    async def handle_connection(self, client: ClientConnection) -> None:
        """Handles the clients' connections"""
        self._LOGGER.info("Connection opened to [%s]", client.id)
        try:
            async for message in client:
                self._LOGGER.info(
                    "Receieved message [%s] from [%s]", message, client.id
                )
                response = self.handle_connection_message(client, message)
                if response:
                    await client.send(json.dumps(response))
        except (ConnectionClosedError, ConnectionClosedOK):
            self._LOGGER.info("Connection closed to [%s]", client.id)
        finally:
            self._LOGGER.info("Removing [%s] from all channels", client.id)
            self.remove_from_channels(client)

    def remove_from_channels(self, client: ClientConnection) -> None:
        """Removes a client from all channels"""
        with self.__channels_lock:
            for channel in self.__channels:
                unsubscribe_all(client, channel)

    def handle_connection_message(self, client: ClientConnection, message: str) -> dict:
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
            return None
        if message_parts[0] not in acceptable_actions:
            self._LOGGER.error("Action [%s] is not acceptable.", message_parts[0])
            return None
        if message_parts[1] not in acceptable_channels:
            self._LOGGER.error("Channel [%s] is not acceptable.", message_parts[1])
            return None
        if message_parts[2] == "*":
            instruments = self.market_realtime_data.get_all_instruments()
            isins = [x.identification.isin for x in instruments]
        else:
            isins = message_parts[2].split(",")
            fake_isin = next((x for x in isins if len(x) != 12), None)
            if fake_isin:
                self._LOGGER.error("Isin [%s] is not acceptable.", fake_isin)
                return None
            instruments = self.market_realtime_data.get_instruments(isins)
        channel_action_func = self.get_channel_action_func(
            message_parts[0], message_parts[1]
        )
        initial_data_func = self.get_initial_data_func(
            message_parts[0], message_parts[1]
        )
        initial_data = {}
        with self.__channels_lock:
            for counter, isin in enumerate(isins):
                channel = next((x for x in self.__channels if x.isin == isin), None)
                if not channel:
                    channel = InstrumentChannel(isin)
                    self.__channels.append(channel)
                    self._LOGGER.info("New channel for [%s]", isin)
                channel_action_func(client, channel)
                if instruments[counter]:
                    initial_data[isin] = initial_data_func(instruments[counter])
        return initial_data

    def get_channel_action_func(
        self, action: str, channel: str
    ) -> Callable[[ClientConnection, InstrumentChannel], None]:
        """Returns the function for handling the subscriptions"""
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

    def get_initial_data_func(
        self, action: str, channel: str
    ) -> Callable[[Instrument], None]:
        """Returns the method for getting the initial data after subscription"""
        return_values = {
            "1": {
                "all": instrument_data_all,
                "trade": instrument_data_trade,
                "orderbook": instrument_data_orderbook,
                "clienttype": instrument_data_clienttype,
            },
            "0": {
                "all": lambda x: None,
                "trade": lambda x: None,
                "orderbook": lambda x: None,
                "clienttype": lambda x: None,
            },
        }
        return return_values[action][channel]

    async def serve_websocket(self) -> None:
        """Serves the websocket for the project"""
        self._LOGGER.info("Serving has started.")
        async with serve(
            self.handle_connection, self.websocket_host, self.websocket_port
        ):
            await sleep_until(MARKET_END_TIME)
        self._LOGGER.info("Serving has ended.")
