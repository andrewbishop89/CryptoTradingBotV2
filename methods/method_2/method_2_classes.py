from dataclasses import dataclass
import threading
import time
import logging
import sys

from helper_functions.websocket_func import *


class MethodLock:
    """Contains all locks for a method thread."""
    def __init__(self, unlimited=False):
        self.profit_file = threading.Lock()
        self.active_trade = threading.Lock() if (not unlimited) else FakeLock()
    
@dataclass
class FakeLock:
    """Lock that doesn't do anything when referenced."""
    def locked(self):
        return False
    def acquire(self, timeout=None):
        return
    def release(self):
        return
    
@dataclass
class DataThread:
    """Local data thread for a single token."""
    symbol: str #symbol of token to trade
    intervals: list #list of intervals of websocket streams to start
    limit: int #amount of klines per kline stream
    locks: dict=None #list of all locks for each interval websocket stream, keys are interval, values are thread locks
    streams: dict=None #list of all websocket stream threads for each interval websocket stream, keys are interval, values are websocket threads
    
    def create_locks(self):
        """Initiate all thread locks for websocket threads."""
        for interval in self.intervals:
            self.locks[interval] = threading.Lock()
    
    def reset_websockets(self):
        """Start all websocket threads."""
        for interval in self.intervals:
            self.streams[interval] = connect_websocket(self.symbol, interval, self.locks[interval], self.limit)
    
    def connect_websockets(self):
        """Initializes all locks and websocket threads to start program."""
        self.create_locks()
        self.reset_websockets()
    
    def wait_for_start(self):
        """Waits until all websocket threads have begun."""
        while True:
            for lock in self.locks:
                if not lock.locked():
                    break
            time.sleep(1)
            
    def check_stream_status(self):
        """Checks websocket streams and restarts if died.""" #TODO during daily timer, thread could break resulting in double threads going at same time
        for interval in self.intervals:
            if not self.streams[interval].is_alive():
                logger.info(f"Restarting {self.symbol}/{interval} Websocket.")
                self.streams[interval] = connect_websocket(self.symbol, "1h", self.locks[interval], self.limit)
            
@dataclass(frozen=True)
class Parameters: # containing all the trade information for the whole program on all threads
    symbols: list # list of symbols to trade
    locks: list # list of locks to use in program
    risk_multiplier: float # risk factor for take profit on each trade
    profit_split_ratio: float # amount of profit split and sold on each take profit
    low_w: int = 8 # short EMA window
    mid_w: int = 13 # medium EMA window
    high_w: int = 21 # long EMA window
    min_profit: float = 0.25 # smallest potential profit percent
    real_money: bool = ("real" in sys.argv) # bool for real money or paper money
    sleep_time: int = 2 # amount of time waited inbetween each loop
    trade_quote_qty: float = None # amount of money traded per trade

@dataclass
class Data: # containing the trade data for each live trade
    # Pre Trade Data
    symbol: str
    
    # During Trade Data
    buy_price: float
    profit_price: float
    stop_price: float
    std_5m: float
    volume_24h: float
    volume_rel: float
    price_24h: float
    buy_time: int
    
    # Post Trade Data
    profit: float
    sell_price: float
    sell_time: int
    side: str
    real: bool
    
@dataclass
class Trade:
    data: Data
    parameters: Parameters
    
    def buy(self):
        return
    
    def sell(self):
        return