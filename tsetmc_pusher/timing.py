"""This modules holds the necessary timing parameters for the project's operations"""
import asyncio
from datetime import time, datetime, timedelta


MORNING_STARTUP_TIME: time = time(hour=7, minute=0, second=0)
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
    time_delta = datetime.combine(datetime.today(), wakeup_at) - datetime.now()
    await asyncio.sleep(time_delta.total_seconds())


async def sleep_until_tomorrow() -> None:
    """Sleep until tomorrow"""
    time_delta = (
        datetime.combine(datetime.today(), MORNING_STARTUP_TIME)
        + timedelta(days=1)
        - datetime.now()
    )
    await asyncio.sleep(time_delta.total_seconds())
