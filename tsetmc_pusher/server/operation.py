"""
This module contains the operational classes in this project 
"""

import asyncio
import logging
from datetime import datetime
import httpx
from tse_utils import tsetmc
from tse_utils.tsetmc.models import TsetmcScrapeException
from tsetmc_pusher.server.repository import MarketRealtimeData
from tsetmc_pusher.server.websocket import TsetmcWebsocket
from tsetmc_pusher.server.timing import (
    sleep_until,
    MARKET_END_TIME,
    MARKET_START_TIME,
    CRAWL_SLEEP_SECONDS,
    TRADE_DATA_TIMEOUT_MAX,
    TRADE_DATA_TIMEOUT_MIN,
    TRADE_DATA_TIMEOUT_STEP,
    CLIENT_TYPE_TIMEOUT_MAX,
    CLIENT_TYPE_TIMEOUT_MIN,
    CLIENT_TYPE_TIMEOUT_STEP,
)


class TsetmcOperator:
    """This module is responsible for continuously crawling TSETMC"""

    _LOGGER = logging.getLogger(__name__)

    def __init__(self, websocket_host: str, websocket_port: int):
        self.market_realtime_date: MarketRealtimeData = MarketRealtimeData()
        self.websocket = TsetmcWebsocket(
            market_realtime_data=self.market_realtime_date,
            websocket_host=websocket_host,
            websocket_port=websocket_port,
        )
        self.__trade_data_timeout: float = TRADE_DATA_TIMEOUT_MIN
        self.__client_type_timeout: float = CLIENT_TYPE_TIMEOUT_MIN
        self.__tsetmc_scraper = tsetmc.TsetmcScraper()

    async def __update_trade_data(self) -> None:
        """Updates trade data from TSETMC"""
        self._LOGGER.info(
            "Trade data catch started, timeout: %.2f", self.__trade_data_timeout
        )
        trade_data = await self.__tsetmc_scraper.get_market_watch(
            # The following line has been removed because of a bug in TSETMC server \
            # that ignores updates on some instruments, including options
            # h_even=self.__max_trade_time_int, ref_id=self.__max_order_row_id
            timeout=self.__trade_data_timeout
        )
        if trade_data:
            self.market_realtime_date.apply_new_trade_data(trade_data)

    @classmethod
    def next_market_watch_request_ids(cls, trade_data) -> tuple[int, int]:
        """Extracts the maximum trade time and orderbook row id"""
        max_order_row_id = max(
            max(y.row_id for y in x.orderbook.rows) for x in trade_data if x.orderbook
        )
        max_trade_time = max(x.last_trade_time for x in trade_data)
        max_trade_time_int = (
            max_trade_time.hour * 10000
            + max_trade_time.minute * 100
            + max_trade_time.second
        )
        return max_trade_time_int, max_order_row_id

    async def __perform_trade_data_loop(self) -> None:
        """Perform the trade data tasks for the market open time"""
        while datetime.now().time() < MARKET_END_TIME:
            try:
                await self.__update_trade_data()
                await asyncio.sleep(CRAWL_SLEEP_SECONDS)
                self.__trade_data_timeout = max(
                    TRADE_DATA_TIMEOUT_MIN,
                    self.__trade_data_timeout - TRADE_DATA_TIMEOUT_STEP,
                )
            except (
                ValueError,
                TsetmcScrapeException,
                httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.ConnectError,
                httpx.ReadTimeout,
            ) as ex:
                self._LOGGER.error("Exception on catching trade data: %s", repr(ex))
                self.__trade_data_timeout = min(
                    TRADE_DATA_TIMEOUT_MAX,
                    self.__trade_data_timeout + TRADE_DATA_TIMEOUT_STEP,
                )

    async def __update_client_type(self) -> None:
        """Updates client type from TSETMC"""
        self._LOGGER.info(
            "Client type catch started, timeout: %.2f", self.__client_type_timeout
        )
        client_type = await self.__tsetmc_scraper.get_client_type_all(
            timeout=self.__client_type_timeout
        )
        if client_type:
            self.market_realtime_date.apply_new_client_type(client_type)

    async def __perform_client_type_loop(self) -> None:
        """Perform the client type tasks for the market open time"""
        while datetime.now().time() < MARKET_END_TIME:
            try:
                await self.__update_client_type()
                await asyncio.sleep(CRAWL_SLEEP_SECONDS)
                self.__client_type_timeout = max(
                    CLIENT_TYPE_TIMEOUT_MIN,
                    self.__client_type_timeout - CLIENT_TYPE_TIMEOUT_STEP,
                )
            except (
                ValueError,
                TsetmcScrapeException,
                httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.ConnectError,
                httpx.ReadTimeout,
            ) as ex:
                self._LOGGER.error("Exception on catching client type: %s", repr(ex))
                self.__client_type_timeout = min(
                    CLIENT_TYPE_TIMEOUT_MAX,
                    self.__client_type_timeout + CLIENT_TYPE_TIMEOUT_STEP,
                )

    async def market_time_operations(self) -> None:
        """Groups the different market time operations"""
        group = asyncio.gather(
            self.__perform_trade_data_loop(),
            self.__perform_client_type_loop(),
            self.websocket.serve_websocket(),
        )
        await asyncio.wait_for(group, timeout=None)

    async def perform_daily(self) -> None:
        """Daily tasks for the crawler are called from here"""
        self._LOGGER.info("Daily tasks are starting.")
        await sleep_until(MARKET_START_TIME)
        self._LOGGER.info("Market is starting.")
        await self.market_time_operations()
