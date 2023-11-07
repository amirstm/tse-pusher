"""Manual test for telegram_task library"""
import os
import logging
from datetime import datetime, time, timedelta
from logging.handlers import TimedRotatingFileHandler


def main():
    """Manually testing the pusher"""
    logger = logging.getLogger("tsetmc_pusher")
    formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s: %(message)s")
    logger.setLevel(logging.INFO)
    log_file_path = "logs/log_"
    file_handler = TimedRotatingFileHandler(
        filename=log_file_path, when="midnight", backupCount=30
    )
    file_handler.suffix = "%Y_%m_%d.log"
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


if __name__ == "__main__":
    main()
