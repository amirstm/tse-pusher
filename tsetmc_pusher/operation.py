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

    @classmethod
    async def sleep(cls, wakeup_at: time):
        """Sleep until appointed time"""
        timedelta = datetime.combine(datetime.today(), wakeup_at) - datetime.now()
        await asyncio.sleep(timedelta)

    async def perform_daily(self):
        """Daily tasks for the crawler are called from here"""
        self._LOGGER.info("Daily tasks are starting.")
        await self.sleep(self.MARKET_START_TIME)
