"""
This module contains the necessary codes for the TSETMC pusher's client.
"""
import json
import logging
import asyncio
from threading import Lock
from datetime import datetime
from websockets import client
from websockets.exceptions import ConnectionClosedError
from websockets.sync.client import ClientConnection
from tse_utils.models.instrument import Instrument, InstrumentIdentification
from enum import Enum


class SubscriptionType(Enum):
    """Client subsctiption type identifier"""

    ALL = "all"
    TRADE = "trade"
    ORDERBOOK = "orderbook"
    CLIENTTYPE = "clienttype"


class TsetmcClient:
    """
The class used for connecting to the TSETMC pusher websocket \
and subscribe to its realtime data
    """

    _LOGGER: logging.Logger = logging.getLogger(__name__)
    _OPERATION_RECONNECT_WAIT: int = 5

    def __init__(
        self,
        websocket_host: str,
        websocket_port: int,
        subscribed_instruments: list[Instrument] = None,
        global_subscriber: bool = False,
        subscription_type: SubscriptionType = SubscriptionType.ALL,
    ):
        self.websocket_host: str = websocket_host
        self.websocket_port: int = websocket_port
        self.__websocket: ClientConnection = None
        self.__subscribed_instruments: list[Instrument] = (
            subscribed_instruments if subscribed_instruments else []
        )
        self.__subscribed_instruments_lock: Lock = Lock()
        self.subscription_type: SubscriptionType = subscription_type
        self.operation_flag: bool = False
        self.global_subscriber: bool = global_subscriber

    async def listen(self) -> None:
        """Listens to websocket updates"""
        while self.operation_flag:
            message = await self.__websocket.recv()
            self._LOGGER.debug("Client received: %s", message)
            self.process_message(message=message)

    def process_message(self, message: str) -> None:
        """Processes a new message received from websocket"""
        message_js = json.loads(message)
        for isin, channels in message_js.items():
            instrument = self.get_subscribed_instrument(isin)
            for channel, data in channels.items():
                match channel:
                    case "thresholds":
                        self.__message_thresholds(instrument, data)
                    case "trade":
                        self.__message_trade(instrument, data)
                    case "orderbook":
                        self.__message_orderbook(instrument, data)
                    case "clienttype":
                        self.__message_clienttype(instrument, data)
                    case _:
                        self._LOGGER.fatal("Unknown message channel: %s", channel)

    def get_subscribed_instrument(self, isin) -> Instrument:
        """Gets the subscribed instrument by Isin"""
        with self.__subscribed_instruments_lock:
            instrument = next(
                (
                    x
                    for x in self.__subscribed_instruments
                    if x.identification.isin == isin
                ),
                None,
            )
            if instrument is None:
                instrument = Instrument(InstrumentIdentification(isin=isin))
                self.__subscribed_instruments.append(instrument)
        return instrument

    def __message_thresholds(self, instrument: Instrument, data: list) -> None:
        """Handles a threshold update message"""
        instrument.order_limitations.max_price = int(data[0])
        instrument.order_limitations.min_price = int(data[1])

    def __message_trade(self, instrument: Instrument, data: list) -> None:
        """Handles a trade update message"""
        instrument.intraday_trade_candle.close_price = int(data[0])
        instrument.intraday_trade_candle.last_price = int(data[1])
        instrument.intraday_trade_candle.last_trade_datetime = datetime.fromisoformat(
            data[2]
        )
        instrument.intraday_trade_candle.max_price = int(data[3])
        instrument.intraday_trade_candle.min_price = int(data[4])
        instrument.intraday_trade_candle.open_price = int(data[5])
        instrument.intraday_trade_candle.previous_price = int(data[6])
        instrument.intraday_trade_candle.trade_num = int(data[7])
        instrument.intraday_trade_candle.trade_value = int(data[8])
        instrument.intraday_trade_candle.trade_volume = int(data[9])

    def __message_orderbook(self, instrument: Instrument, data: list) -> None:
        """Handles an orderbook update message"""
        for row in data:
            rn = int(row[0])
            instrument.orderbook.rows[rn].demand.num = int(row[1])
            instrument.orderbook.rows[rn].demand.price = int(row[2])
            instrument.orderbook.rows[rn].demand.volume = int(row[3])
            instrument.orderbook.rows[rn].supply.num = int(row[4])
            instrument.orderbook.rows[rn].supply.price = int(row[5])
            instrument.orderbook.rows[rn].supply.volume = int(row[6])

    def __message_clienttype(self, instrument: Instrument, data: list) -> None:
        """Handles an orderbook update message"""
        if data[0] is None:
            return
        instrument.client_type.legal.buy.num = int(data[0])
        instrument.client_type.legal.buy.volume = int(data[1])
        instrument.client_type.legal.sell.num = int(data[2])
        instrument.client_type.legal.sell.volume = int(data[3])
        instrument.client_type.natural.buy.num = int(data[4])
        instrument.client_type.natural.buy.volume = int(data[5])
        instrument.client_type.natural.sell.num = int(data[6])
        instrument.client_type.natural.sell.volume = int(data[7])

    async def subscribe(self) -> None:
        """Subscribe to the channels for the appointed instruemtns"""
        if self.global_subscriber:
            self._LOGGER.info("Client is subscribing to data for all instruments.")
            isins = "*"
        else:
            with self.__subscribed_instruments_lock:
                self._LOGGER.info(
                    "Client is subscribing to data for %d instruments.",
                    len(self.__subscribed_instruments),
                )
                isins = ",".join(
                    [x.identification.isin for x in self.__subscribed_instruments]
                )
        await self.__websocket.send(f"1.{self.subscription_type.value}.{isins}")

    async def start_operation(self) -> None:
        """Start connecting to the websocket and listening for updates for a single loop"""
        self._LOGGER.info("Client is starting its single-try operation.")
        self.operation_flag = True
        await self.__operation_single_try()

    async def infinite_operation(self) -> None:
        """Start connecting to the websocket and listening for updates in an infinite loop"""
        self._LOGGER.info("Client is starting its infinite operation.")
        self.operation_flag = True
        while self.operation_flag:
            try:
                await self.__operation_single_try()
            except (OSError, ConnectionClosedError) as exc:
                self._LOGGER.error("Connection error: %s", repr(exc))
                await asyncio.sleep(self._OPERATION_RECONNECT_WAIT)

    async def __operation_single_try(self):
        """Does a single try on connecting to server"""
        self._LOGGER.info("Client is connecting.")
        async with client.connect(
            f"ws://{self.websocket_host}:{self.websocket_port}"
        ) as self.__websocket:
            self._LOGGER.info("Client is connected.")
            await self.subscribe()
            await self.listen()

    def stop_operation(self) -> None:
        """Stops the infinite loop for operations"""
        self.operation_flag = False
