"""
This module contains the operational classes in this project 
"""

import asyncio
import logging
from datetime import time, datetime
import httpx
from tse_utils import tsetmc
from tsetmc_pusher.repository import MarketRealtimeData


MARKET_START_TIME: time = time(hour=8, minute=30, second=0)
MARKET_END_TIME: time = time(hour=15, minute=0, second=0)
CRAWL_SLEEP_SECONDS: float = 1


class TsetmcRealtimeCrawler:
    """This module is responsible for continuously crawling TSETMC"""

    _LOGGER = logging.getLogger(__name__)

    def __init__(self):
        self.market_realtime_date: MarketRealtimeData = MarketRealtimeData()
        self.__trade_data_timeout: int = 500
        self.__tsetmc_scraper = tsetmc.TsetmcScraper()
        self.__max_trade_time_int: int = 0
        self.__max_order_row_id: int = 0

    @classmethod
    async def sleep(cls, wakeup_at: time):
        """Sleep until appointed time"""
        timedelta = datetime.combine(datetime.today(), wakeup_at) - datetime.now()
        await asyncio.sleep(timedelta.total_seconds())

    async def __update_trade_data(self):
        """Updates trade data from TSETMC"""
        self._LOGGER.info(
            "Trade data catch started, timeout : %d", self.__trade_data_timeout
        )
        market_watch_data = await self.__tsetmc_scraper.get_market_watch(
            # The following line has been removed because of a bug in TSETMC server \
            # that ignores updates on some instruments, including options
            # h_even=self.__max_trade_time_int, ref_id=self.__max_order_row_id
        )
        if market_watch_data:
            (
                self.__max_trade_time_int,
                self.__max_order_row_id,
            ) = self.next_market_watch_request_ids(market_watch_data)
            self.market_realtime_date.apply_new_market_watch_trade_data(
                market_watch_data
            )

    @classmethod
    def next_market_watch_request_ids(cls, market_watch_data):
        """Extracts the maximum trade time and orderbook row id"""
        max_order_row_id = max(
            max(y.row_id for y in x.orderbook.rows)
            for x in market_watch_data
            if x.orderbook
        )
        max_trade_time = max(x.last_trade_time for x in market_watch_data)
        max_trade_time_int = (
            max_trade_time.hour * 10000
            + max_trade_time.minute * 100
            + max_trade_time.second
        )
        return max_trade_time_int, max_order_row_id

    async def __perform_trade_data_loop(self):
        """Perform the tasks for the market open time"""
        while datetime.now().time() < MARKET_END_TIME:
            try:
                await self.__update_trade_data()
                await asyncio.sleep(CRAWL_SLEEP_SECONDS)
            except (ValueError, httpx.TimeoutException, httpx.NetworkError) as ex:
                self._LOGGER.error("Exception on catching trade data: %s", repr(ex))

    async def perform_daily(self):
        """Daily tasks for the crawler are called from here"""
        self._LOGGER.info("Daily tasks are starting.")
        await self.sleep(MARKET_START_TIME)
        self._LOGGER.info("Market is starting.")
        await self.__perform_trade_data_loop()
