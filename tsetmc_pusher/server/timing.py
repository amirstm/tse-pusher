"""This modules holds the necessary timing parameters for the project's operations"""
import asyncio
from datetime import time, datetime


MARKET_START_TIME: time = time(hour=8, minute=30, second=0)
MARKET_END_TIME: time = time(hour=15, minute=0, second=0)
CRAWL_SLEEP_SECONDS: float = 0.5
TRADE_DATA_TIMEOUT_MAX: float = 1.5
TRADE_DATA_TIMEOUT_MIN: float = 0.5
TRADE_DATA_TIMEOUT_STEP: float = 0.25
CLIENT_TYPE_TIMEOUT_MAX: float = 3.0
CLIENT_TYPE_TIMEOUT_MIN: float = 0.5
CLIENT_TYPE_TIMEOUT_STEP: float = 0.25


async def sleep_until(wakeup_at: time) -> None:
    """Sleep until appointed time"""
    timedelta = datetime.combine(datetime.today(), wakeup_at) - datetime.now()
    await asyncio.sleep(timedelta.total_seconds())
