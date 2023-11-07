"""
This module contains the classes needed for keeping realtime market data 
"""
from dataclasses import dataclass
from tse_utils.models import instrument


@dataclass
class MarketRealtimeData:
    """Holds all realtime data for market"""

    instruments: list[instrument.InstrumentRealtime]

    def __init__(self):
        self.instruments = []
