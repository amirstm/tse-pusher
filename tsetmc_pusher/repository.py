"""
This module contains the classes needed for keeping realtime market data 
"""
import asyncio
import threading
from typing import Callable, Awaitable
from datetime import datetime
from tse_utils.models.instrument import Instrument, InstrumentIdentification
from tse_utils.models.realtime import OrderBookRow, ClientType
from tse_utils.tsetmc import MarketWatchTradeData, MarketWatchClientTypeData


class MarketRealtimeData:
    """Holds all realtime data for market"""

    def __init__(self):
        self.__instruments: list[Instrument] = []
        self.__instruments_lock: threading.Lock = threading.Lock()
        self.pusher_trade_data: Callable[
            [list[Instrument]], Awaitable[None]
        ] = lambda x: asyncio.sleep(0)
        self.pusher_orderbook_data: Callable[
            [list[tuple[Instrument, list[int]]]], Awaitable[None]
        ] = lambda x: asyncio.sleep(0)
        self.pusher_clienttype_data: Callable[
            [list[Instrument]], Awaitable[None]
        ] = lambda x: asyncio.sleep(0)

    def apply_new_client_type(
        self, client_type: list[MarketWatchClientTypeData]
    ) -> None:
        """Applies the new client type to the repository"""
        updated_clienttype_instruments = []
        with self.__instruments_lock:
            for mwi in client_type:
                instrument = next(
                    (
                        x
                        for x in self.__instruments
                        if x.identification.tsetmc_code == mwi.tsetmc_code
                    ),
                    None,
                )
                if instrument and instrument.client_type != mwi:
                    self.update_instrument_client_type(instrument.client_type, mwi)
        threading.Thread(
            target=asyncio.run,
            args=(self.pusher_clienttype_data(updated_clienttype_instruments),),
            daemon=True,
        ).start()

    def update_instrument_client_type(
        self, instrument_ct: ClientType, mwi_ct: ClientType
    ):
        """Update an instrument's client type data"""
        instrument_ct.legal.buy.num = mwi_ct.legal.buy.num
        instrument_ct.legal.buy.volume = mwi_ct.legal.buy.volume
        instrument_ct.legal.sell.num = mwi_ct.legal.sell.num
        instrument_ct.legal.sell.volume = mwi_ct.legal.sell.volume
        instrument_ct.natural.buy.num = mwi_ct.natural.buy.num
        instrument_ct.natural.buy.volume = mwi_ct.natural.buy.volume
        instrument_ct.natural.sell.num = mwi_ct.natural.sell.num
        instrument_ct.natural.sell.volume = mwi_ct.natural.sell.volume

    def apply_new_trade_data(self, trade_data: list[MarketWatchTradeData]) -> None:
        """Applies the new trade data to the repository"""
        updated_trade_instruments = []
        updated_orderbook_instruments = []
        with self.__instruments_lock:
            for mwi in trade_data:
                instrument = next(
                    (
                        x
                        for x in self.__instruments
                        if x.identification.isin == mwi.identification.isin
                    ),
                    None,
                )
                if not instrument:
                    instrument = Instrument(
                        InstrumentIdentification(
                            isin=mwi.identification.isin,
                            tsetmc_code=mwi.identification.tsetmc_code,
                            ticker=mwi.identification.ticker,
                            name_persian=mwi.identification.name_persian,
                        )
                    )
                    self.__instruments.append(instrument)
                if not (
                    instrument.intraday_trade_candle.last_trade_datetime
                    and instrument.intraday_trade_candle.last_trade_datetime.time()
                    == mwi.last_trade_time
                ):
                    self.update_instrument_trade_data(instrument, mwi)
                    updated_trade_instruments.append(instrument)
                updated_rows = []
                for rn, row in enumerate(mwi.orderbook.rows):
                    if row != instrument.orderbook.rows[rn]:
                        self.update_instrument_orderbook_row(
                            instrument.orderbook.rows[rn], row
                        )
                        updated_rows.append(rn)
                if updated_rows:
                    updated_orderbook_instruments.append((instrument, updated_rows))
        threading.Thread(
            target=asyncio.run,
            args=(self.pusher_trade_data(updated_trade_instruments),),
            daemon=True,
        ).start()
        threading.Thread(
            target=asyncio.run,
            args=(self.pusher_orderbook_data(updated_orderbook_instruments),),
            daemon=True,
        ).start()

    def update_instrument_orderbook_row(
        self, instrument_obr: OrderBookRow, mwi_obr: OrderBookRow
    ):
        """Update a single row in instrument's order book"""
        instrument_obr.demand.num = mwi_obr.demand.num
        instrument_obr.demand.volume = mwi_obr.demand.volume
        instrument_obr.demand.price = mwi_obr.demand.price
        instrument_obr.supply.num = mwi_obr.supply.num
        instrument_obr.supply.volume = mwi_obr.supply.volume
        instrument_obr.supply.price = mwi_obr.supply.price

    def update_instrument_trade_data(
        self, instrument: Instrument, mwi: MarketWatchTradeData
    ) -> None:
        """Updates trade data for a single instrument"""
        instrument.order_limitations.max_price = mwi.price_thresholds.max_price
        instrument.order_limitations.min_price = mwi.price_thresholds.min_price
        instrument.intraday_trade_candle.previous_price = (
            mwi.intraday_trade_candle.previous_price
        )
        instrument.intraday_trade_candle.close_price = (
            mwi.intraday_trade_candle.close_price
        )
        instrument.intraday_trade_candle.last_price = (
            mwi.intraday_trade_candle.last_price
        )
        instrument.intraday_trade_candle.open_price = (
            mwi.intraday_trade_candle.open_price
        )
        instrument.intraday_trade_candle.max_price = mwi.intraday_trade_candle.max_price
        instrument.intraday_trade_candle.min_price = mwi.intraday_trade_candle.min_price
        instrument.intraday_trade_candle.trade_volume = (
            mwi.intraday_trade_candle.trade_volume
        )
        instrument.intraday_trade_candle.trade_value = (
            mwi.intraday_trade_candle.trade_value
        )
        instrument.intraday_trade_candle.trade_num = mwi.intraday_trade_candle.trade_num
        instrument.intraday_trade_candle.last_trade_datetime = datetime.combine(
            datetime.today(), mwi.last_trade_time
        )

    def get_instruments(self, isins: list[str]) -> list[Instrument]:
        """Returns instruments matching with a list of isins"""
        with self.__instruments_lock:
            instruments = [
                next(
                    (x for x in self.__instruments if x.identification.isin == y), None
                )
                for y in isins
            ]
        return instruments
