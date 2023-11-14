"""This modules holds the necessary timing parameters for the project's operations"""
import asyncio
from datetime import time, datetime


MARKET_START_TIME: time = time(hour=8, minute=30, second=0)
MARKET_END_TIME: time = time(hour=19, minute=0, second=0)  # TODO : fix
CRAWL_SLEEP_SECONDS: float = 1


async def sleep_until(wakeup_at: time) -> None:
    """Sleep until appointed time"""
    timedelta = datetime.combine(datetime.today(), wakeup_at) - datetime.now()
    await asyncio.sleep(timedelta.total_seconds())
