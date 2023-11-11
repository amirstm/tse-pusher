"""
This module contains the operational classes in this project 
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import time, datetime
from tse_utils import tsetmc
from tsetmc_pusher.repository import MarketRealtimeData


@dataclass
class TsetmcRealtimeCrawlerTiminigs:
    """Holds timing params for operations"""

    MARKET_START_TIME: time = time(hour=8, minute=30, second=0)
    MARKET_END_TIME: time = time(hour=15, minute=0, second=0)
    CRAWL_SLEEP_SECONDS: float = 0.1


class TsetmcRealtimeCrawler(TsetmcRealtimeCrawlerTiminigs):
    """This module is responsible for continuously crawling TSETMC"""

    _LOGGER = logging.getLogger(__name__)

    def __init__(self):
        self.market_realtime_date = MarketRealtimeData()
        self.__trade_data_timeout = 500
        self.__tsetmc_scraper = tsetmc.TsetmcScraper()

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
        market_watch_data = await self.__tsetmc_scraper.get_market_watch()
        print(market_watch_data)

    async def __perform_trade_data_loop(self):
        """Perform the tasks for the market open time"""
        while datetime.now().time() < self.MARKET_END_TIME:
            try:
                await self.__update_trade_data()
                await asyncio.sleep(TsetmcRealtimeCrawlerTiminigs.CRAWL_SLEEP_SECONDS)
            except Exception as ex:
                pass

    async def perform_daily(self):
        """Daily tasks for the crawler are called from here"""
        self._LOGGER.info("Daily tasks are starting.")
        await self.sleep(self.MARKET_START_TIME)
        self._LOGGER.info("Market is starting.")
        await self.__perform_trade_data_loop()
