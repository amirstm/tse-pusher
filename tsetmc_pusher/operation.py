"""
This module contains the operational classes in this project 
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import time, datetime
from tsetmc_pusher.repository import MarketRealtimeData


@dataclass
class TsetmcRealtimeCrawlerTiminigs:
    """Holds timing params for operations"""

    MARKET_START_TIME: time = time(hour=8, minute=30, second=0)
    MARKET_END_TIME: time = time(hour=15, minute=0, second=0)


class TsetmcRealtimeCrawler(TsetmcRealtimeCrawlerTiminigs):
    """This module is responsible for continuously crawling TSETMC"""

    _LOGGER = logging.getLogger(__name__)

    def __init__(self):
        self.market_realtime_date = MarketRealtimeData()
        self.__trade_data_timeout = 500

    @classmethod
    async def sleep(cls, wakeup_at: time):
        """Sleep until appointed time"""
        timedelta = datetime.combine(datetime.today(), wakeup_at) - datetime.now()
        await asyncio.sleep(timedelta)

    async def __update_trade_data(self):
        """Updates trade data from TSETMC"""
        self._LOGGER.info(
            "Trade data catch started, timeout : %d", self.__trade_data_timeout
        )

    async def __perform_trade_data_loop(self):
        """Perform the tasks for the market open time"""
        while datetime.now().time() < self.MARKET_END_TIME:
            try:
                await self.__update_trade_data()
            except Exception as ex:
                pass

    async def perform_daily(self):
        """Daily tasks for the crawler are called from here"""
        self._LOGGER.info("Daily tasks are starting.")
        await self.sleep(self.MARKET_START_TIME)
        self._LOGGER.info("Market is starting.")
        await self.__perform_trade_data_loop()
