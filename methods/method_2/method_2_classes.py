from dataclasses import dataclass
import threading
import sys


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